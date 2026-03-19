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
from core.tools.advanced_risk_metrics import advanced_risk_metrics, ADVANCED_RISK_METRICS_SCHEMA
from core.tools.cumulative_return import cumulative_return, CUMULATIVE_RETURN_SCHEMA
from core.tools.holdings_performance import holdings_performance, HOLDINGS_PERFORMANCE_SCHEMA
from core.tools.bond_analytics import bond_analytics, BOND_ANALYTICS_SCHEMA
from core.tools.stock_style_analysis import stock_style_analysis, STOCK_STYLE_ANALYSIS_SCHEMA
from core.tools.portfolio_fundamentals import portfolio_fundamentals, PORTFOLIO_FUNDAMENTALS_SCHEMA
from core.tools.simulate_rebalance import simulate_rebalance, SIMULATE_REBALANCE_SCHEMA
from core.tools.goal_score import goal_score, GOAL_SCORE_SCHEMA

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
    "advanced_risk_metrics": advanced_risk_metrics,
    "cumulative_return": cumulative_return,
    "holdings_performance": holdings_performance,
    "bond_analytics": bond_analytics,
    "stock_style_analysis": stock_style_analysis,
    "portfolio_fundamentals": portfolio_fundamentals,
    "simulate_rebalance": simulate_rebalance,
    "goal_score": goal_score,
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
    ADVANCED_RISK_METRICS_SCHEMA,
    CUMULATIVE_RETURN_SCHEMA,
    HOLDINGS_PERFORMANCE_SCHEMA,
    BOND_ANALYTICS_SCHEMA,
    STOCK_STYLE_ANALYSIS_SCHEMA,
    PORTFOLIO_FUNDAMENTALS_SCHEMA,
    SIMULATE_REBALANCE_SCHEMA,
    GOAL_SCORE_SCHEMA,
]
