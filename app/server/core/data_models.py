"""
Backend API contract types for WealthLens.

These Pydantic models define the shape of all data flowing through the system:
agent state, API responses, and tool outputs.

NOTE: DB models (core/db/models.py) define storage. These data models define
API contracts and agent data shapes. They coexist.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field
from copilotkit import CopilotKitState


# ---------------------------------------------------------------------------
# Agent State — single source of truth (replaces duplicates in main.py & agent.py)
# ---------------------------------------------------------------------------


class WealthLensState(CopilotKitState):
    """Agent state for WealthLens."""
    tools: list
    messages: list
    widgets: list
    tool_logs: list
    households: list
    active_conversation_id: str
    plan: list
    extraction_results: list
    enrichment_cache: dict


# ---------------------------------------------------------------------------
# Portfolio data shapes (API-level, NOT the SQLModel DB models)
# ---------------------------------------------------------------------------


class HoldingData(BaseModel):
    """A single holding within an account."""
    symbol: str = ""
    name: str = ""
    quantity: float = 0
    market_value: float = 0
    current_price: float = 0
    mer: float = 0
    asset_class: str = ""
    sector: str = ""
    country: str = ""
    geographic_exposure: str = ""
    market_cap_class: str = ""
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    pe_ratio: Optional[float] = None


class AccountData(BaseModel):
    """A single investment account."""
    name: str = ""
    type: str = ""
    total_value: float = 0
    holdings: list[HoldingData] = Field(default_factory=list)


class HouseholdData(BaseModel):
    """A household / institution grouping of accounts."""
    institution: str = "Unknown"
    accounts: list[AccountData] = Field(default_factory=list)
    confidence: float = 0


# ---------------------------------------------------------------------------
# API response types
# ---------------------------------------------------------------------------


class UploadStatementResponse(BaseModel):
    """Response from POST /upload-statement."""
    institution: str = "Unknown"
    accounts: list[AccountData] = Field(default_factory=list)
    confidence: float = 0
    widgets: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Widget types (Python equivalents of frontend widgets.ts)
# ---------------------------------------------------------------------------


class GridPosition(BaseModel):
    """Grid layout position for a widget."""
    col: int
    row: int
    colSpan: Optional[int] = None
    rowSpan: Optional[int] = None


class WidgetSpec(BaseModel):
    """A dashboard widget specification."""
    id: str
    type: str  # pie | bar | line | table | gauge | summary | treemap | sankey
    title: str
    data: Any
    gridPosition: Optional[GridPosition] = None
    confidence: Optional[float] = None


# ---------------------------------------------------------------------------
# Tool result types
# ---------------------------------------------------------------------------


class ToolResult(BaseModel):
    """Base return shape for all tools."""
    error: Optional[str] = None


class AllocationItem(BaseModel):
    name: str
    value: float
    percentage: float


class AllocationResult(ToolResult):
    """Return shape for compute_allocation."""
    group_by: str = ""
    total_value: float = 0
    allocation: list[AllocationItem] = Field(default_factory=list)


class FeeBreakdownItem(BaseModel):
    name: str
    symbol: str = ""
    market_value: float = 0
    mer_percent: float = 0
    annual_fee: float = 0
    account: str = ""


class FeeAlternative(BaseModel):
    symbol: str
    name: str
    mer: float


class HighCostFlag(BaseModel):
    name: str
    symbol: str = ""
    current_mer: float = 0
    annual_fee: float = 0
    market_value: float = 0
    suggested_alternative: Optional[FeeAlternative] = None
    annual_savings: Optional[float] = None
    ten_year_fee_drag: Optional[float] = None


class FeeResult(ToolResult):
    """Return shape for compute_fees."""
    total_value: float = 0
    total_annual_fees: float = 0
    weighted_avg_mer: float = 0
    fee_breakdown: list[FeeBreakdownItem] = Field(default_factory=list)
    high_cost_flags: Optional[list[HighCostFlag]] = None
    total_potential_annual_savings: Optional[float] = None
    high_cost_threshold: Optional[float] = None


class RiskFlag(BaseModel):
    flag: str
    detail: str
    severity: str  # low | medium | high


class ConcentrationDetail(BaseModel):
    symbol: str
    value: float
    percentage: float


class BreakdownItem(BaseModel):
    name: str
    value: float
    percentage: float


class RiskResult(ToolResult):
    """Return shape for portfolio_risk."""
    total_value: float = 0
    holdings_count: int = 0
    weighted_beta: Optional[float] = None
    beta_coverage_pct: float = 0
    risk_classification: str = "Unknown"
    top_5_concentration: Optional[dict[str, Any]] = None
    sector_breakdown: list[BreakdownItem] = Field(default_factory=list)
    geographic_breakdown: list[BreakdownItem] = Field(default_factory=list)
    home_bias_detected: bool = False
    canada_allocation_pct: float = 0
    market_cap_breakdown: list[BreakdownItem] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class HoldingIncomeItem(BaseModel):
    symbol: str
    name: str = ""
    market_value: float = 0
    yield_pct: float = 0
    annual_income: float = 0
    monthly_income: float = 0
    income_type: str = ""
    account: str = ""


class IncomeTypeBreakdown(BaseModel):
    type: str
    annual_income: float = 0
    percentage: float = 0


class IncomeAccountBreakdown(BaseModel):
    account: str
    annual_income: float = 0
    percentage: float = 0


class TaxNote(BaseModel):
    note: str
    detail: str
    impact: str  # positive | negative


class IncomeResult(ToolResult):
    """Return shape for income_analysis."""
    total_value: float = 0
    weighted_yield_pct: float = 0
    total_annual_income: float = 0
    total_monthly_income: float = 0
    holdings_with_yield: int = 0
    holdings_income: list[HoldingIncomeItem] = Field(default_factory=list)
    income_by_type: list[IncomeTypeBreakdown] = Field(default_factory=list)
    income_by_account: list[IncomeAccountBreakdown] = Field(default_factory=list)
    tax_notes: list[TaxNote] = Field(default_factory=list)
