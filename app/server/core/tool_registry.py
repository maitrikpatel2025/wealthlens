"""
Tool registry partitioning for multi-agent specialist system.
Maps each specialist to its subset of tools from the central TOOL_FUNCTIONS registry.
"""

from core.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

# Specialist → tool name mapping
SPECIALIST_TOOLS: dict[str, list[str]] = {
    "risk_analyst": [
        "portfolio_risk",
        "detect_concentration",
        "advanced_risk_metrics",
        "bond_analytics",
    ],
    "fee_optimizer": [
        "compute_fees",
        "detect_overlap",
    ],
    "income_analyst": [
        "income_analysis",
        "compute_allocation",
    ],
    "macro_strategist": [
        "scenario_simulation",
        "compare_performance",
        "cumulative_return",
        "holdings_performance",
    ],
    "synthesizer": [
        "rank_insights",
        "generate_report",
        "portfolio_graph",
    ],
}

# Tools available to all specialists
SHARED_TOOLS: list[str] = [
    "compute_allocation",
    "add_widget",
    "update_widget",
    "remove_widget",
    "stock_style_analysis",
    "portfolio_fundamentals",
    "simulate_rebalance",
    "goal_score",
    "auto_dashboard",
]

# Schema lookup by name
_SCHEMA_BY_NAME: dict[str, dict] = {s["name"]: s for s in TOOL_SCHEMAS}


def get_tools_for_specialist(name: str) -> tuple[dict, list[dict]]:
    """
    Return (functions_dict, schemas_list) for the given specialist.
    Includes specialist-specific tools + shared tools.
    """
    tool_names = set(SPECIALIST_TOOLS.get(name, []) + SHARED_TOOLS)
    functions = {n: TOOL_FUNCTIONS[n] for n in tool_names if n in TOOL_FUNCTIONS}
    schemas = [_SCHEMA_BY_NAME[n] for n in tool_names if n in _SCHEMA_BY_NAME]
    return functions, schemas


def get_tools_for_synthesizer() -> tuple[dict, list[dict]]:
    """Return tools available to the synthesizer agent."""
    return get_tools_for_specialist("synthesizer")


def get_tool_descriptions_for(tool_schemas: list[dict]) -> str:
    """Build a concise tool description block from a list of schemas."""
    lines = []
    for schema in tool_schemas:
        name = schema["name"]
        desc = schema.get("description", "")
        params = schema.get("parameters", {}).get("properties", {})
        param_names = ", ".join(params.keys()) if params else "none"
        lines.append(f"- {name}({param_names}): {desc}")
    return "\n".join(lines)
