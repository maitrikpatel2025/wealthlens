"""
WealthLens multi-agent system (M4).
Graph: START → supervisor → specialists (parallel) → persona_sim (deep only) → synthesize → respond → END

Quick mode: supervisor → 1 specialist → respond
Deep mode:  supervisor → all specialists parallel → 4 personas parallel → synthesizer → respond
"""

import asyncio
import json
import time
import uuid
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from ag_ui.core import StateDeltaEvent, EventType

from core.data_models import WealthLensState
from core.prompts import system_prompt
from core.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
from core.tool_registry import (
    get_tools_for_specialist,
    get_tools_for_synthesizer,
    get_tool_descriptions_for,
)
from core.specialist_prompts import (
    SUPERVISOR_PROMPT,
    RISK_ANALYST_PROMPT,
    FEE_OPTIMIZER_PROMPT,
    INCOME_ANALYST_PROMPT,
    MACRO_STRATEGIST_PROMPT,
    SYNTHESIZER_PROMPT,
    PERSONA_PROMPTS,
)


# ── Utility functions (reused from M3) ─────────────────────────────────────

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
    """Build a compact text summary of all households."""
    if not households:
        return "No portfolio data uploaded yet."
    lines = []
    for h in households:
        inst = (
            h.get("institution", {}).get("name", "Unknown")
            if isinstance(h.get("institution"), dict)
            else h.get("institution", "Unknown")
        )
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


def _get_user_profile_section(user_profile: dict) -> str:
    """Format user profile for prompts."""
    if not user_profile:
        return ""
    parts = []
    if user_profile.get("age"):
        parts.append(f"Age: {user_profile['age']}")
    if user_profile.get("risk_tolerance"):
        parts.append(f"Risk tolerance: {user_profile['risk_tolerance']}")
    if user_profile.get("goal"):
        parts.append(f"Goal: {user_profile['goal']}")
    if user_profile.get("time_horizon"):
        parts.append(f"Time horizon: {user_profile['time_horizon']} years")
    return f"\n\nUSER PROFILE:\n" + "\n".join(parts) if parts else ""


def _extract_tool_calls(content: str) -> list[dict]:
    """Extract ALL tool call JSONs from markdown code blocks."""
    calls = []
    search_from = 0
    while True:
        try:
            start = content.index("```json", search_from)
            end = content.index("```", start + 7)
            json_str = content[start + 7 : end].strip()
            parsed = json.loads(json_str)
            if "tool" in parsed:
                calls.append(parsed)
            search_from = end + 3
        except (ValueError, json.JSONDecodeError):
            break
    return calls


def _merge_widgets(existing: list, new_widgets: list) -> list:
    """Merge new widgets into existing list, deduplicating by title."""
    widgets = list(existing)
    for nw in new_widgets:
        title = nw.get("title", "")
        found = next((w for w in widgets if w.get("title") == title), None)
        if found:
            found["data"] = nw["data"]
            if "confidence" in nw:
                found["confidence"] = nw["confidence"]
            if "type" in nw:
                found["type"] = nw["type"]
        else:
            nw["id"] = f"w-{uuid.uuid4().hex[:8]}"
            widgets.append(nw)
    return widgets


# ── Activity helpers ────────────────────────────────────────────────────────

def _make_activity(agent: str, message: str, tool: str = "") -> dict:
    return {
        "id": f"act-{uuid.uuid4().hex[:8]}",
        "agent": agent,
        "status": "active",
        "message": message,
        "tool": tool,
        "started_at": time.time(),
    }


def _complete_activity(activity: dict, message: str = "") -> dict:
    activity = dict(activity)
    activity["status"] = "completed"
    activity["completed_at"] = time.time()
    if message:
        activity["message"] = message
    return activity


# ── Specialist runner ───────────────────────────────────────────────────────

SPECIALIST_PROMPT_MAP = {
    "risk_analyst": RISK_ANALYST_PROMPT,
    "fee_optimizer": FEE_OPTIMIZER_PROMPT,
    "income_analyst": INCOME_ANALYST_PROMPT,
    "macro_strategist": MACRO_STRATEGIST_PROMPT,
}

MAX_SPECIALIST_LOOPS = 3


async def _run_specialist(
    specialist_name: str,
    state: dict,
    emit_event=None,
) -> dict:
    """
    Run a specialist agent with its own planner-tool loop.
    Returns {"summary": str, "widgets": list, "activities": list}.
    """
    prompt = SPECIALIST_PROMPT_MAP.get(specialist_name, "")
    tool_fns, tool_schemas = get_tools_for_specialist(specialist_name)
    tool_desc = get_tool_descriptions_for(tool_schemas)
    household_summary = _summarize_households(state.get("households", []))
    profile_section = _get_user_profile_section(state.get("user_profile", {}))

    # Get the user's latest question
    user_question = ""
    for msg in reversed(state.get("messages", [])):
        role = getattr(msg, "role", "user")
        if role == "user":
            user_question = getattr(msg, "content", str(msg))
            break

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    messages = [
        {
            "role": "system",
            "content": (
                f"{prompt}\n\n"
                f"AVAILABLE TOOLS:\n{tool_desc}\n\n"
                f"Use ```json blocks for tool calls.\n\n"
                f"PORTFOLIO DATA:\n{household_summary}{profile_section}"
            ),
        },
        {"role": "user", "content": user_question},
    ]

    widgets = list(state.get("widgets", []))
    activities = []
    all_tool_results = []

    activity = _make_activity(specialist_name, f"{specialist_name} analyzing...")
    activities.append(activity)

    # Emit activity start
    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[{"op": "replace", "path": "/agent_activities/-", "value": activity}],
        ))

    for loop_i in range(MAX_SPECIALIST_LOOPS):
        response = await llm.ainvoke(messages)
        content = response.content

        tool_calls = _extract_tool_calls(content)
        if not tool_calls:
            # No more tools — this is the specialist's summary
            activities.append(
                _complete_activity(activity, f"{specialist_name} complete")
            )
            if emit_event:
                emit_event(StateDeltaEvent(
                    type=EventType.STATE_DELTA,
                    delta=[{"op": "replace", "path": "/agent_activities/-",
                            "value": _complete_activity(activity, f"{specialist_name} complete")}],
                ))
            return {
                "summary": content,
                "widgets": widgets,
                "activities": activities,
                "tool_results": all_tool_results,
            }

        # Execute tools
        loop_results = []
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            tool_args = tc.get("args", {})

            tool_activity = _make_activity(specialist_name, f"Running {tool_name}", tool=tool_name)
            activities.append(tool_activity)

            fn = tool_fns.get(tool_name) or TOOL_FUNCTIONS.get(tool_name)
            if fn:
                try:
                    current_state = dict(state)
                    current_state["widgets"] = widgets
                    result = fn(tool_args, current_state)
                except Exception as e:
                    result = {"error": str(e)}
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            # Handle widgets
            if "widgets" in result:
                widgets = result["widgets"]
            if "new_widgets" in result:
                widgets = _merge_widgets(widgets, result["new_widgets"])

            # Emit widget update
            if emit_event:
                emit_event(StateDeltaEvent(
                    type=EventType.STATE_DELTA,
                    delta=[{"op": "replace", "path": "/widgets", "value": widgets}],
                ))

            result_summary = {k: v for k, v in result.items() if k not in ("new_widgets", "widgets")}
            loop_results.append({"tool": tool_name, "result": result_summary})
            all_tool_results.append({"tool": tool_name, "result": result_summary})

            activities.append(_complete_activity(tool_activity, f"Completed {tool_name}"))

        # Feed results back to specialist LLM
        results_json = json.dumps(loop_results, default=str)[:2000]
        messages.append({"role": "assistant", "content": content})
        messages.append({
            "role": "user",
            "content": f"[Tool Results]:\n{results_json}\n\nWidgets auto-created. Summarize findings or call another tool.",
        })

    # Fallback: max loops reached
    activities.append(_complete_activity(activity, f"{specialist_name} complete (max loops)"))
    return {
        "summary": f"{specialist_name} completed analysis.",
        "widgets": widgets,
        "activities": activities,
        "tool_results": all_tool_results,
    }


# ── Persona runner ──────────────────────────────────────────────────────────

async def _run_persona(
    persona_name: str,
    state: dict,
    specialist_summaries: str,
) -> dict:
    """Run an investor persona evaluation."""
    prompt = PERSONA_PROMPTS.get(persona_name, "")
    household_summary = _summarize_households(state.get("households", []))
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    messages = [
        {
            "role": "system",
            "content": f"{prompt}\n\nPORTFOLIO DATA:\n{household_summary}",
        },
        {
            "role": "user",
            "content": f"Here are the specialist analysis results:\n\n{specialist_summaries}\n\nProvide your perspective.",
        },
    ]

    response = await llm.ainvoke(messages)
    return {"persona": persona_name, "view": response.content}


# ── Graph nodes ─────────────────────────────────────────────────────────────

async def supervisor_node(state: WealthLensState, config: dict = None) -> dict:
    """Supervisor: route to specialists and decide quick vs deep mode."""
    config = config or {}
    emit_event = config.get("configurable", {}).get("emit_event", None)

    household_summary = _summarize_households(state.get("households", []))

    # Get the user's latest question
    user_question = ""
    for msg in reversed(state.get("messages", [])):
        role = getattr(msg, "role", "user")
        if role == "user":
            user_question = getattr(msg, "content", str(msg))
            break

    # If no portfolio data, skip multi-agent — respond directly
    if not state.get("households"):
        return {
            "analysis_mode": "quick",
            "active_specialists": [],
            "agent_activities": [
                _make_activity("supervisor", "No portfolio data — guiding user to upload")
            ],
        }

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {
            "role": "user",
            "content": f"User question: {user_question}\n\nPortfolio summary: {household_summary[:500]}",
        },
    ]

    activity = _make_activity("supervisor", "Routing to specialists...")
    activities = [activity]

    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {"op": "replace", "path": "/agent_activities", "value": activities},
                {"op": "replace", "path": "/active_specialists", "value": []},
            ],
        ))

    response = await llm.ainvoke(messages)
    content = response.content

    # Parse supervisor routing decision
    specialists = []
    mode = "quick"
    try:
        parsed = json.loads(
            content[content.index("{") : content.rindex("}") + 1]
        )
        specialists = parsed.get("specialists", [])
        mode = parsed.get("mode", "quick")
    except (ValueError, json.JSONDecodeError):
        # Fallback: single specialist based on keywords
        specialists = ["risk_analyst"]
        mode = "quick"

    activities.append(
        _complete_activity(activity, f"Routing to {', '.join(specialists)} ({mode} mode)")
    )

    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {"op": "replace", "path": "/agent_activities", "value": activities},
                {"op": "replace", "path": "/active_specialists", "value": specialists},
                {"op": "replace", "path": "/analysis_mode", "value": mode},
            ],
        ))

    return {
        "analysis_mode": mode,
        "active_specialists": specialists,
        "agent_activities": activities,
    }


async def specialists_node(state: WealthLensState, config: dict = None) -> dict:
    """Run specialist agents — parallel in deep mode, single in quick mode."""
    config = config or {}
    emit_event = config.get("configurable", {}).get("emit_event", None)
    specialists = state.get("active_specialists", [])
    mode = state.get("analysis_mode", "quick")

    if not specialists:
        # No specialists needed (e.g., no portfolio data)
        return {}

    # Run specialists
    if mode == "deep" and len(specialists) > 1:
        # Parallel execution
        tasks = [
            _run_specialist(name, dict(state), emit_event)
            for name in specialists
        ]
        results = await asyncio.gather(*tasks)
    else:
        # Sequential (quick mode — usually just 1)
        results = []
        for name in specialists:
            result = await _run_specialist(name, dict(state), emit_event)
            results.append(result)

    # Merge all results
    specialist_results = {}
    all_activities = list(state.get("agent_activities", []))
    widgets = list(state.get("widgets", []))

    for name, result in zip(specialists, results):
        specialist_results[name] = {
            "summary": result["summary"],
            "tool_results": result.get("tool_results", []),
        }
        all_activities.extend(result.get("activities", []))
        # Merge widgets from each specialist
        widgets = _merge_widgets(widgets, [
            w for w in result.get("widgets", [])
            if not any(ew.get("title") == w.get("title") for ew in widgets)
        ])

    # Emit updated widgets
    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {"op": "replace", "path": "/widgets", "value": widgets},
                {"op": "replace", "path": "/agent_activities", "value": all_activities},
            ],
        ))

    return {
        "specialist_results": specialist_results,
        "widgets": widgets,
        "agent_activities": all_activities,
    }


async def persona_node(state: WealthLensState, config: dict = None) -> dict:
    """Run investor persona simulations (deep mode only)."""
    config = config or {}
    mode = state.get("analysis_mode", "quick")

    if mode != "deep":
        return {}

    specialist_results = state.get("specialist_results", {})
    summaries = "\n\n".join(
        f"=== {name.upper()} ===\n{r['summary']}"
        for name, r in specialist_results.items()
    )

    # Run all personas in parallel
    tasks = [
        _run_persona(name, dict(state), summaries)
        for name in PERSONA_PROMPTS
    ]
    results = await asyncio.gather(*tasks)

    persona_results = [r for r in results]

    activities = list(state.get("agent_activities", []))
    for r in persona_results:
        activities.append(
            _complete_activity(
                _make_activity("persona", f"{r['persona']} perspective"),
                f"{r['persona']} complete",
            )
        )

    return {
        "persona_results": persona_results,
        "agent_activities": activities,
    }


async def synthesize_node(state: WealthLensState, config: dict = None) -> dict:
    """Synthesize specialist results into a unified response."""
    config = config or {}
    emit_event = config.get("configurable", {}).get("emit_event", None)
    mode = state.get("analysis_mode", "quick")
    specialist_results = state.get("specialist_results", {})
    persona_results = state.get("persona_results", [])

    # Quick mode: use specialist summary directly, no extra LLM call
    if mode == "quick" and specialist_results:
        first_result = next(iter(specialist_results.values()), {})
        summary = first_result.get("summary", "Analysis complete.")

        # Build the final response message
        messages = list(state.get("messages", []))
        messages.append(AIMessage(content=summary))

        return {"messages": messages}

    # Deep mode: synthesizer LLM combines everything
    if not specialist_results:
        return {}

    activity = _make_activity("synthesizer", "Synthesizing analysis...")
    activities = list(state.get("agent_activities", []))
    activities.append(activity)

    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[{"op": "replace", "path": "/agent_activities", "value": activities}],
        ))

    specialist_text = "\n\n".join(
        f"=== {name.upper()} ===\n{r['summary']}"
        for name, r in specialist_results.items()
    )

    persona_text = ""
    if persona_results:
        persona_text = "\n\n" + "\n\n".join(
            f"--- {r['persona']} ---\n{r['view']}"
            for r in persona_results
        )

    # Get user question
    user_question = ""
    for msg in reversed(state.get("messages", [])):
        role = getattr(msg, "role", "user")
        if role == "user":
            user_question = getattr(msg, "content", str(msg))
            break

    # Check if synthesizer should generate a report
    synth_fns, synth_schemas = get_tools_for_synthesizer()
    tool_desc = get_tool_descriptions_for(synth_schemas)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    synth_messages = [
        {
            "role": "system",
            "content": (
                f"{SYNTHESIZER_PROMPT}\n\n"
                f"AVAILABLE TOOLS:\n{tool_desc}\n\n"
                f"Use ```json blocks for tool calls if needed."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original question: {user_question}\n\n"
                f"SPECIALIST RESULTS:\n{specialist_text}"
                f"{persona_text}\n\n"
                f"Synthesize the above into a unified response. "
                f"If the user asked for a report, use generate_report. "
                f"Otherwise, provide a concise 3-5 sentence summary of the key findings."
            ),
        },
    ]

    response = await llm.ainvoke(synth_messages)
    content = response.content

    # Check if synthesizer wants to call tools (e.g., generate_report)
    widgets = list(state.get("widgets", []))
    tool_calls = _extract_tool_calls(content)
    if tool_calls:
        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            tool_args = tc.get("args", {})
            fn = synth_fns.get(tool_name) or TOOL_FUNCTIONS.get(tool_name)
            if fn:
                try:
                    current_state = dict(state)
                    current_state["widgets"] = widgets
                    result = fn(tool_args, current_state)
                    if "new_widgets" in result:
                        widgets = _merge_widgets(widgets, result["new_widgets"])
                    if "widgets" in result:
                        widgets = result["widgets"]
                except Exception:
                    pass

        if emit_event:
            emit_event(StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[{"op": "replace", "path": "/widgets", "value": widgets}],
            ))

        # Strip tool call blocks from response
        import re
        content = re.sub(r'```json\s*\{[^`]*\}\s*```', '', content).strip()

    activities.append(_complete_activity(activity, "Synthesis complete"))

    if emit_event:
        emit_event(StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[{"op": "replace", "path": "/agent_activities", "value": activities}],
        ))

    # Build final message
    messages = list(state.get("messages", []))
    messages.append(AIMessage(content=content))

    return {
        "messages": messages,
        "widgets": widgets,
        "agent_activities": activities,
    }


async def respond_node(state: WealthLensState, config: dict = None) -> dict:
    """Terminal node — handles the no-portfolio-data case."""
    config = config or {}
    specialist_results = state.get("specialist_results", {})

    # If we already have a synthesized response, just end
    if specialist_results:
        return {}

    # No portfolio data — use original single-agent flow for guidance
    emit_event = config.get("configurable", {}).get("emit_event", None)
    tool_desc = _build_tool_descriptions()
    household_summary = _summarize_households(state.get("households", []))
    profile_section = _get_user_profile_section(state.get("user_profile", {}))

    formatted = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n\n"
                f"AVAILABLE TOOLS:\n{tool_desc}\n\n"
                f"When you need to use a tool, respond with a JSON block:\n"
                f"```json\n{{\"tool\": \"tool_name\", \"args\": {{...}}}}\n```\n\n"
                f"When you have enough information to respond to the user, just respond in plain text.\n\n"
                f"PORTFOLIO DATA:\n{household_summary}{profile_section}\n\n"
                f"Current widgets: {len(state.get('widgets', []))} widgets on dashboard."
            ),
        },
    ]
    for msg in state.get("messages", []):
        role = getattr(msg, "role", "user")
        content = getattr(msg, "content", str(msg))
        if role in ("user", "assistant", "system"):
            formatted.append({"role": role, "content": content})

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    response = await llm.ainvoke(formatted)

    messages = list(state.get("messages", []))
    messages.append(response)

    # Check for tool calls in response (single-agent fallback)
    tool_calls = _extract_tool_calls(response.content)
    if tool_calls:
        widgets = list(state.get("widgets", []))
        tool_logs = list(state.get("tool_logs", []))

        for tc in tool_calls:
            tool_name = tc.get("tool", "")
            tool_args = tc.get("args", {})
            fn = TOOL_FUNCTIONS.get(tool_name)
            if fn:
                try:
                    current_state = dict(state)
                    current_state["widgets"] = widgets
                    result = fn(tool_args, current_state)
                    if "widgets" in result:
                        widgets = result["widgets"]
                    if "new_widgets" in result:
                        widgets = _merge_widgets(widgets, result["new_widgets"])
                except Exception:
                    pass

        if emit_event:
            emit_event(StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[{"op": "replace", "path": "/widgets", "value": widgets}],
            ))

        return {"messages": messages, "widgets": widgets}

    return {"messages": messages}


def _route_after_supervisor(state: WealthLensState) -> Literal["specialists", "respond"]:
    """Route: if specialists assigned → run them. Otherwise → respond directly."""
    specialists = state.get("active_specialists", [])
    if specialists:
        return "specialists"
    return "respond"


def _route_after_specialists(state: WealthLensState) -> Literal["persona_sim", "synthesize"]:
    """Route: deep mode → personas, quick mode → synthesize."""
    mode = state.get("analysis_mode", "quick")
    if mode == "deep":
        return "persona_sim"
    return "synthesize"


async def agent_graph():
    """Build and compile the WealthLens multi-agent graph."""
    graph = StateGraph(WealthLensState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("specialists", specialists_node)
    graph.add_node("persona_sim", persona_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("respond", respond_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges("supervisor", _route_after_supervisor, {
        "specialists": "specialists",
        "respond": "respond",
    })

    graph.add_conditional_edges("specialists", _route_after_specialists, {
        "persona_sim": "persona_sim",
        "synthesize": "synthesize",
    })

    graph.add_edge("persona_sim", "synthesize")
    graph.add_edge("synthesize", END)
    graph.add_edge("respond", END)

    return graph.compile()
