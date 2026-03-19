"""
WealthLens planning-based agent (M3).
Graph: START → planner → router → {execute_tool | respond | end}
                                     execute_tool → planner (loop)
"""

import json
import uuid
from typing import Any, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from ag_ui.core import StateDeltaEvent, EventType
from core.data_models import WealthLensState
from core.prompts import system_prompt
from core.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS


def _build_tool_descriptions() -> str:
    """Build a concise tool description block for the system prompt."""
    lines = []
    for schema in TOOL_SCHEMAS:
        name = schema["name"]
        desc = schema.get("description", "")
        params = schema.get("parameters", {}).get("properties", {})
        param_names = ", ".join(params.keys()) if params else "none"
        lines.append(f"- {name}({param_names}): {desc}")
    return "\n".join(lines)


def _summarize_households(households: list) -> str:
    """Build a compact text summary of all households so the LLM sees every account."""
    if not households:
        return "No portfolio data uploaded yet."
    lines = []
    for h in households:
        inst = h.get("institution", {}).get("name", "Unknown") if isinstance(h.get("institution"), dict) else h.get("institution", "Unknown")
        lines.append(f"Institution: {inst}")
        for acct in h.get("accounts", []):
            acct_type = acct.get("type", acct.get("name", "Unknown"))
            total = acct.get("total_value", 0)
            lines.append(f"  Account: {acct_type} — ${total:,.2f}")
            for holding in acct.get("holdings", []):
                sym = holding.get("symbol", "?")
                name = holding.get("name", "")
                qty = holding.get("quantity", 0)
                val = holding.get("market_value", holding.get("value", 0))
                mer = holding.get("mer", 0)
                price = holding.get("current_price", 0)
                acls = holding.get("asset_class", "")
                parts = [f"{sym}"]
                if name:
                    parts.append(f'"{name}"')
                parts.append(f"qty={qty}")
                parts.append(f"val=${val:,.2f}")
                if price:
                    parts.append(f"price=${price:.2f}")
                if mer:
                    parts.append(f"MER={mer:.2f}%")
                if acls:
                    parts.append(f"class={acls}")
                # CFA-level enriched fields
                beta = holding.get("beta")
                if beta:
                    parts.append(f"beta={beta}")
                div_yield = holding.get("dividend_yield")
                if div_yield:
                    parts.append(f"yield={div_yield}%")
                country = holding.get("country", "")
                if country:
                    parts.append(f"country={country}")
                exposure = holding.get("geographic_exposure", "")
                if exposure:
                    parts.append(f"exposure={exposure}")
                cap_class = holding.get("market_cap_class", "")
                if cap_class:
                    parts.append(f"cap={cap_class}")
                sector = holding.get("sector", "")
                if sector and sector != "Unknown":
                    parts.append(f"sector={sector}")
                pe = holding.get("pe_ratio")
                if pe:
                    parts.append(f"P/E={pe}")
                lines.append(f"    - {' | '.join(parts)}")
    return "\n".join(lines)


def _format_messages(state: dict) -> list:
    """Convert state messages to LLM-compatible format."""
    formatted = []
    tool_desc = _build_tool_descriptions()
    household_summary = _summarize_households(state.get("households", []))
    user_profile = state.get("user_profile", {})
    profile_section = ""
    if user_profile:
        profile_parts = []
        if user_profile.get("age"):
            profile_parts.append(f"Age: {user_profile['age']}")
        if user_profile.get("risk_tolerance"):
            profile_parts.append(f"Risk tolerance: {user_profile['risk_tolerance']}")
        if user_profile.get("goal"):
            profile_parts.append(f"Goal: {user_profile['goal']}")
        if user_profile.get("time_horizon"):
            profile_parts.append(f"Time horizon: {user_profile['time_horizon']} years")
        if profile_parts:
            profile_section = f"\n\nUSER PROFILE:\n" + "\n".join(profile_parts)

    formatted.append({
        "role": "system",
        "content": f"{system_prompt}\n\nAVAILABLE TOOLS:\n{tool_desc}\n\nWhen you need to use a tool, respond with a JSON block:\n```json\n{{\"tool\": \"tool_name\", \"args\": {{...}}}}\n```\n\nWhen you have enough information to respond to the user, just respond in plain text.\n\nPORTFOLIO DATA:\n{household_summary}{profile_section}\n\nCurrent widgets: {len(state.get('widgets', []))} widgets on dashboard."
    })

    for msg in state.get("messages", []):
        role = getattr(msg, "role", "user")
        content = getattr(msg, "content", str(msg))
        if role in ("user", "assistant", "system"):
            formatted.append({"role": role, "content": content})

    return formatted


async def planner_node(state: WealthLensState, config: dict) -> dict:
    """
    Planner: analyzes the conversation and decides whether to call a tool or respond.
    Returns updated messages with assistant response.
    """
    emit_event = config.get("configurable", {}).get("emit_event", None)
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

    messages = _format_messages(state)
    response = await llm.ainvoke(messages)

    updated_messages = list(state.get("messages", []))
    updated_messages.append(response)

    return {"messages": updated_messages}


MAX_TOOL_LOOPS = 6  # safety limit to prevent infinite planner→tool cycles


def router(state: WealthLensState) -> Literal["execute_tool", "respond"]:
    """
    Route based on planner output.
    If the assistant's last message contains a tool call JSON block, route to execute_tool.
    Otherwise, route to respond (end).
    Includes recursion guard: stops after MAX_TOOL_LOOPS tool executions.
    """
    messages = state.get("messages", [])
    if not messages:
        return "respond"

    # Count how many [Tool Results] messages exist (each represents one tool loop)
    tool_result_count = sum(
        1 for m in messages
        if getattr(m, "content", "").startswith("[Tool Results]")
    )
    if tool_result_count >= MAX_TOOL_LOOPS:
        return "respond"

    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")

    # Check for tool call pattern
    if "```json" in content and '"tool"' in content:
        return "execute_tool"

    return "respond"


async def execute_tool_node(state: WealthLensState, config: dict) -> dict:
    """
    Extract and execute ALL tool calls from assistant message.
    Tools that return 'new_widgets' auto-add widgets to the dashboard.
    Emits state deltas immediately so the frontend updates in real time.
    """
    messages = list(state.get("messages", []))
    last_msg = messages[-1]
    content = getattr(last_msg, "content", "")

    # Extract ALL tool calls from the message
    tool_calls = _extract_tool_calls(content)
    if not tool_calls:
        return {"messages": messages}

    emit_event = config.get("configurable", {}).get("emit_event", None)
    tool_logs = list(state.get("tool_logs", []))
    widgets = list(state.get("widgets", []))
    all_results = []

    for tool_call in tool_calls:
        tool_name = tool_call.get("tool", "")
        tool_args = tool_call.get("args", {})

        log_id = len(tool_logs) + 1
        tool_logs.append({"id": log_id, "message": f"Running {tool_name}...", "status": "processing"})

        fn = TOOL_FUNCTIONS.get(tool_name)
        if fn:
            try:
                # Pass current widgets so tools see the latest list
                current_state = dict(state)
                current_state["widgets"] = widgets
                result = fn(tool_args, current_state)
            except Exception as e:
                result = {"error": str(e)}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        # Handle full widget replacement (from add_widget/update_widget/remove_widget)
        if "widgets" in result:
            widgets = result["widgets"]

        # Handle new_widgets: append with dedup by title
        if "new_widgets" in result:
            for nw in result["new_widgets"]:
                title = nw.get("title", "")
                existing = next((w for w in widgets if w.get("title") == title), None)
                if existing:
                    existing["data"] = nw["data"]
                    if "confidence" in nw:
                        existing["confidence"] = nw["confidence"]
                    if "type" in nw:
                        existing["type"] = nw["type"]
                else:
                    nw["id"] = f"w-{uuid.uuid4().hex[:8]}"
                    widgets.append(nw)

        # Mark log as complete
        for log in tool_logs:
            if log["id"] == log_id:
                log["status"] = "completed"
                log["message"] = f"Completed {tool_name}"

        # Collect result for summary (exclude widget lists to keep it concise)
        result_for_summary = {k: v for k, v in result.items() if k not in ("new_widgets", "widgets")}
        all_results.append({"tool": tool_name, "result": result_for_summary})

    # Emit widget state delta immediately so frontend updates in real time
    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[{"op": "replace", "path": "/widgets", "value": widgets}],
        ))

    # Summarize results for the planner
    results_summary = json.dumps(all_results, default=str)[:3000]
    messages.append(type(last_msg)(
        role="user",
        content=f"[Tool Results]:\n{results_summary}\n\nWidgets have been automatically added/updated on the dashboard. Provide a brief 1-2 sentence summary for the chat. Do NOT call add_widget — widgets are already created."
    ))

    return {
        "messages": messages,
        "tool_logs": tool_logs,
        "widgets": widgets,
    }


async def respond_node(state: WealthLensState, config: dict) -> dict:
    """Terminal node — the planner's last message is the response."""
    return {}


def _extract_tool_calls(content: str) -> list[dict]:
    """Extract ALL tool call JSONs from markdown code blocks."""
    calls = []
    search_from = 0
    while True:
        try:
            start = content.index("```json", search_from)
            end = content.index("```", start + 7)
            json_str = content[start + 7:end].strip()
            parsed = json.loads(json_str)
            if "tool" in parsed:
                calls.append(parsed)
            search_from = end + 3
        except (ValueError, json.JSONDecodeError):
            break
    return calls


async def agent_graph():
    """Build and compile the WealthLens agent graph."""
    graph = StateGraph(WealthLensState)

    graph.add_node("planner", planner_node)
    graph.add_node("execute_tool", execute_tool_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("planner")

    graph.add_conditional_edges("planner", router, {
        "execute_tool": "execute_tool",
        "respond": "respond",
    })

    # After executing a tool, loop back to planner
    graph.add_edge("execute_tool", "planner")
    graph.add_edge("respond", END)

    return graph.compile()
