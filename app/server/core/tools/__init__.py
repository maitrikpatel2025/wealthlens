"""
WealthLens tool registry.
Maps tool names to their execution functions and collects schemas for LLM binding.
"""

from core.tools.compute_allocation import compute_allocation, COMPUTE_ALLOCATION_SCHEMA
from core.tools.compute_fees import compute_fees, COMPUTE_FEES_SCHEMA
from core.tools.detect_overlap import detect_overlap, DETECT_OVERLAP_SCHEMA
from core.tools.detect_concentration import detect_concentration, DETECT_CONCENTRATION_SCHEMA
from core.tools.compare_performance import compare_performance, COMPARE_PERFORMANCE_SCHEMA
from core.tools.rank_insights import rank_insights, RANK_INSIGHTS_SCHEMA
from core.tools.portfolio_risk import portfolio_risk, PORTFOLIO_RISK_SCHEMA
from core.tools.income_analysis import income_analysis, INCOME_ANALYSIS_SCHEMA
from core.tools.widget_tools import add_widget, update_widget, remove_widget, ADD_WIDGET_SCHEMA, UPDATE_WIDGET_SCHEMA, REMOVE_WIDGET_SCHEMA
from core.tools.auto_dashboard import auto_dashboard, AUTO_DASHBOARD_SCHEMA

# Name → function mapping
TOOL_FUNCTIONS = {
    "compute_allocation": compute_allocation,
    "compute_fees": compute_fees,
    "detect_overlap": detect_overlap,
    "detect_concentration": detect_concentration,
    "compare_performance": compare_performance,
    "rank_insights": rank_insights,
    "portfolio_risk": portfolio_risk,
    "income_analysis": income_analysis,
    "add_widget": add_widget,
    "update_widget": update_widget,
    "remove_widget": remove_widget,
    "auto_dashboard": auto_dashboard,
}

# All tool schemas for LLM function calling
TOOL_SCHEMAS = [
    COMPUTE_ALLOCATION_SCHEMA,
    COMPUTE_FEES_SCHEMA,
    DETECT_OVERLAP_SCHEMA,
    DETECT_CONCENTRATION_SCHEMA,
    COMPARE_PERFORMANCE_SCHEMA,
    RANK_INSIGHTS_SCHEMA,
    PORTFOLIO_RISK_SCHEMA,
    INCOME_ANALYSIS_SCHEMA,
    ADD_WIDGET_SCHEMA,
    UPDATE_WIDGET_SCHEMA,
    REMOVE_WIDGET_SCHEMA,
    AUTO_DASHBOARD_SCHEMA,
]
