"""Portfolio report generator: orchestrates existing tools into a markdown report."""

from datetime import datetime

GENERATE_REPORT_SCHEMA = {
    "name": "generate_report",
    "description": (
        "Generate a comprehensive multi-section portfolio analysis report in markdown. "
        "Sections include executive summary, asset allocation, risk analysis, fee analysis, "
        "income analysis, key insights, and recommendations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "include_sections": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "executive_summary",
                        "allocation",
                        "risk",
                        "fees",
                        "income",
                        "insights",
                        "recommendations",
                    ],
                },
                "description": "Sections to include. Defaults to all sections.",
            },
        },
        "required": [],
    },
}

ALL_SECTIONS = [
    "executive_summary",
    "allocation",
    "risk",
    "fees",
    "income",
    "insights",
    "recommendations",
]


def _safe_call(fn, args: dict, state: dict) -> dict:
    """Call a tool function safely, returning empty dict on error."""
    try:
        result = fn(args, state)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception:
        pass
    return {}


def _fmt_currency(val) -> str:
    if val is None:
        return "N/A"
    return f"${val:,.2f}"


def _fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.2f}%"


def _build_executive_summary(state: dict) -> str:
    """Build executive summary from raw portfolio data."""
    households = state.get("households", [])
    total_value = 0
    total_fees = 0
    total_income = 0
    holding_count = 0
    account_count = 0
    beta_sum = 0
    beta_weight = 0

    for h in households:
        for acct in h.get("accounts", []):
            account_count += 1
            for holding in acct.get("holdings", []):
                val = holding.get("market_value", 0)
                mer = holding.get("mer", 0)
                dy = holding.get("dividend_yield", 0) or 0
                b = holding.get("beta")
                total_value += val
                total_fees += val * mer / 100
                total_income += val * dy / 100
                holding_count += 1
                if isinstance(b, (int, float)):
                    beta_sum += b * val
                    beta_weight += val

    weighted_mer = (total_fees / total_value * 100) if total_value > 0 else 0
    weighted_yield = (total_income / total_value * 100) if total_value > 0 else 0
    weighted_beta = (beta_sum / beta_weight) if beta_weight > 0 else None

    lines = [
        "# Executive Summary\n",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Portfolio Value | {_fmt_currency(total_value)} |",
        f"| Number of Accounts | {account_count} |",
        f"| Number of Holdings | {holding_count} |",
        f"| Weighted MER | {_fmt_pct(weighted_mer)} |",
        f"| Annual Fee Drag | {_fmt_currency(total_fees)} |",
        f"| Weighted Yield | {_fmt_pct(weighted_yield)} |",
        f"| Est. Annual Income | {_fmt_currency(total_income)} |",
    ]
    if weighted_beta is not None:
        lines.append(f"| Portfolio Beta | {weighted_beta:.2f} |")
    lines.append("")
    return "\n".join(lines)


def _build_allocation_section(state: dict) -> str:
    """Build asset allocation section."""
    from core.tools.compute_allocation import compute_allocation

    lines = ["# Asset Allocation\n"]

    for group_by, label in [("asset_class", "By Asset Class"), ("sector", "By Sector"), ("geographic_exposure", "By Geography")]:
        result = _safe_call(compute_allocation, {"group_by": group_by}, state)
        breakdown = result.get("breakdown", [])
        if breakdown:
            lines.append(f"## {label}\n")
            lines.append("| Category | Value | Weight |")
            lines.append("|----------|-------|--------|")
            for item in breakdown:
                name = item.get("name", "Unknown")
                value = item.get("value", 0)
                pct = item.get("percent", 0)
                lines.append(f"| {name} | {_fmt_currency(value)} | {_fmt_pct(pct)} |")
            lines.append("")

    return "\n".join(lines)


def _build_risk_section(state: dict) -> str:
    """Build risk analysis section."""
    from core.tools.portfolio_risk import portfolio_risk
    from core.tools.detect_concentration import detect_concentration

    lines = ["# Risk Analysis\n"]

    risk_result = _safe_call(portfolio_risk, {}, state)
    if risk_result:
        beta = risk_result.get("weighted_beta")
        risk_level = risk_result.get("risk_level", "Unknown")
        lines.append(f"**Portfolio Beta:** {f'{beta:.2f}' if isinstance(beta, (int, float)) else 'N/A'}")
        lines.append(f"**Risk Level:** {risk_level}\n")

        risk_flags = risk_result.get("risk_flags", [])
        if risk_flags:
            lines.append("## Risk Flags\n")
            for flag in risk_flags:
                if isinstance(flag, dict):
                    lines.append(f"- **{flag.get('type', 'Risk')}:** {flag.get('message', '')}")
                else:
                    lines.append(f"- {flag}")
            lines.append("")

    conc_result = _safe_call(detect_concentration, {"threshold_percent": 10}, state)
    concentrated = conc_result.get("concentrated_holdings", [])
    if concentrated:
        lines.append("## Concentration Risks\n")
        lines.append("| Holding | Weight | Threshold |")
        lines.append("|---------|--------|-----------|")
        for item in concentrated:
            name = item.get("symbol", item.get("name", "Unknown"))
            weight = item.get("weight_pct", item.get("percent", 0))
            lines.append(f"| {name} | {_fmt_pct(weight)} | >10% |")
        lines.append("")

    return "\n".join(lines)


def _build_fees_section(state: dict) -> str:
    """Build fee analysis section."""
    from core.tools.compute_fees import compute_fees

    lines = ["# Fee Analysis\n"]

    result = _safe_call(compute_fees, {"show_alternatives": True}, state)
    if result:
        weighted_mer = result.get("weighted_mer")
        annual_fees = result.get("annual_fees")
        ten_year = result.get("ten_year_drag")

        lines.append(f"**Weighted MER:** {_fmt_pct(weighted_mer)}")
        lines.append(f"**Annual Fee Drag:** {_fmt_currency(annual_fees)}")
        if ten_year:
            lines.append(f"**10-Year Compounded Impact:** {_fmt_currency(ten_year)}")
        lines.append("")

        holdings = result.get("holdings_fees", result.get("holdings", []))
        if holdings:
            lines.append("## Fee Breakdown by Holding\n")
            lines.append("| Holding | MER | Annual Fee |")
            lines.append("|---------|-----|------------|")
            for h in holdings[:15]:
                symbol = h.get("symbol", "Unknown")
                mer = h.get("mer", 0)
                fee = h.get("annual_fee", 0)
                lines.append(f"| {symbol} | {_fmt_pct(mer)} | {_fmt_currency(fee)} |")
            lines.append("")

    return "\n".join(lines)


def _build_income_section(state: dict) -> str:
    """Build income analysis section."""
    from core.tools.income_analysis import income_analysis

    lines = ["# Income Analysis\n"]

    result = _safe_call(income_analysis, {}, state)
    if result:
        weighted_yield = result.get("weighted_yield")
        annual_income = result.get("annual_income")
        monthly_income = result.get("monthly_income")

        lines.append(f"**Weighted Yield:** {_fmt_pct(weighted_yield)}")
        lines.append(f"**Est. Annual Income:** {_fmt_currency(annual_income)}")
        if monthly_income:
            lines.append(f"**Est. Monthly Income:** {_fmt_currency(monthly_income)}")
        lines.append("")

        by_holding = result.get("income_by_holding", result.get("holdings", []))
        if by_holding:
            lines.append("## Income by Holding\n")
            lines.append("| Holding | Yield | Annual Income |")
            lines.append("|---------|-------|---------------|")
            for h in by_holding[:15]:
                symbol = h.get("symbol", "Unknown")
                dy = h.get("dividend_yield", h.get("yield", 0))
                inc = h.get("annual_income", h.get("income", 0))
                lines.append(f"| {symbol} | {_fmt_pct(dy)} | {_fmt_currency(inc)} |")
            lines.append("")

    return "\n".join(lines)


def _build_insights_section(state: dict) -> str:
    """Build key insights section."""
    from core.tools.rank_insights import rank_insights

    lines = ["# Key Insights\n"]

    result = _safe_call(rank_insights, {}, state)
    insights = result.get("insights", [])
    if insights:
        for i, insight in enumerate(insights[:10], 1):
            if isinstance(insight, dict):
                title = insight.get("title", insight.get("type", f"Insight {i}"))
                desc = insight.get("description", insight.get("message", ""))
                severity = insight.get("severity", insight.get("priority", ""))
                sev_str = f" ({severity})" if severity else ""
                lines.append(f"{i}. **{title}**{sev_str}: {desc}")
            else:
                lines.append(f"{i}. {insight}")
        lines.append("")
    else:
        lines.append("No significant insights detected.\n")

    return "\n".join(lines)


def _build_recommendations_section(state: dict) -> str:
    """Build recommendations section based on gathered data."""
    from core.tools.compute_fees import compute_fees
    from core.tools.portfolio_risk import portfolio_risk
    from core.tools.detect_concentration import detect_concentration

    lines = ["# Recommendations\n"]
    recs = []

    fee_result = _safe_call(compute_fees, {"show_alternatives": True}, state)
    weighted_mer = fee_result.get("weighted_mer", 0)
    if weighted_mer and weighted_mer > 0.5:
        recs.append(f"Consider reducing fees — your weighted MER of {_fmt_pct(weighted_mer)} is above average. Look for lower-cost ETF alternatives.")

    risk_result = _safe_call(portfolio_risk, {}, state)
    beta = risk_result.get("weighted_beta")
    if isinstance(beta, (int, float)) and beta > 1.2:
        recs.append(f"Portfolio beta of {beta:.2f} indicates above-market risk. Consider adding defensive holdings or fixed income to reduce volatility.")

    conc_result = _safe_call(detect_concentration, {"threshold_percent": 15}, state)
    concentrated = conc_result.get("concentrated_holdings", [])
    if concentrated:
        names = ", ".join(c.get("symbol", "Unknown") for c in concentrated[:3])
        recs.append(f"Concentration risk in {names}. Consider diversifying to reduce single-holding risk.")

    if not recs:
        recs.append("Portfolio appears well-balanced. Continue monitoring regularly.")

    lines.append("*These are educational observations, not financial advice. Consult a qualified advisor.*\n")
    for i, rec in enumerate(recs, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    return "\n".join(lines)


SECTION_BUILDERS = {
    "executive_summary": _build_executive_summary,
    "allocation": _build_allocation_section,
    "risk": _build_risk_section,
    "fees": _build_fees_section,
    "income": _build_income_section,
    "insights": _build_insights_section,
    "recommendations": _build_recommendations_section,
}


def generate_report(args: dict, state: dict) -> dict:
    """Generate a comprehensive portfolio report."""
    households = state.get("households", [])
    if not households:
        return {"error": "No portfolio data available. Please upload a brokerage statement first."}

    sections = args.get("include_sections") or ALL_SECTIONS
    sections = [s for s in sections if s in SECTION_BUILDERS]

    # Compute total value for metadata
    total_value = 0
    for h in households:
        for acct in h.get("accounts", []):
            for holding in acct.get("holdings", []):
                total_value += holding.get("market_value", 0)

    # Build markdown
    parts = []
    for section in sections:
        builder = SECTION_BUILDERS.get(section)
        if builder:
            parts.append(builder(state))

    parts.append("---\n")
    parts.append("*This report is for educational purposes only and does not constitute financial advice.*")

    markdown = "\n".join(parts)
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    new_widgets = [
        {
            "type": "report",
            "title": "Portfolio Analysis Report",
            "data": {
                "markdown": markdown,
                "generated_at": generated_at,
                "sections": sections,
                "portfolio_value": round(total_value, 2),
            },
            "gridPosition": {"col": 1, "row": 1, "colSpan": 2},
            "confidence": 0.8,
        },
    ]

    return {
        "generated_at": generated_at,
        "sections": sections,
        "portfolio_value": round(total_value, 2),
        "new_widgets": new_widgets,
    }
