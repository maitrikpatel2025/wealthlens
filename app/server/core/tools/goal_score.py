"""Goal-Based Personalization: score portfolio alignment against financial goals."""

GOAL_SCORE_SCHEMA = {
    "name": "goal_score",
    "description": (
        "Evaluate portfolio alignment against a financial goal (retirement, growth, income, "
        "education, preservation). Returns a composite score (0-100) with component scores "
        "for allocation, fees, diversification, income, and time horizon."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "goal_type": {
                "type": "string",
                "enum": ["retirement", "growth", "income", "education", "preservation"],
                "description": "The financial goal to score against.",
            },
            "age": {
                "type": "number",
                "description": "Investor's current age (used for glide-path adjustment).",
            },
            "risk_tolerance": {
                "type": "string",
                "enum": ["conservative", "moderate", "aggressive"],
                "description": "Self-reported risk tolerance.",
            },
            "target_income": {
                "type": "number",
                "description": "Target annual income from portfolio (for income goal).",
            },
            "time_horizon_years": {
                "type": "number",
                "description": "Years until goal target date.",
            },
        },
        "required": ["goal_type"],
    },
}

# Benchmark targets per goal type
GOAL_BENCHMARKS = {
    "retirement": {
        "equity_pct": 60, "fi_pct": 35, "cash_pct": 5,
        "max_mer": 0.50, "min_yield": 2.0, "min_holdings": 5,
    },
    "growth": {
        "equity_pct": 85, "fi_pct": 10, "cash_pct": 5,
        "max_mer": 0.40, "min_yield": 0.5, "min_holdings": 4,
    },
    "income": {
        "equity_pct": 40, "fi_pct": 50, "cash_pct": 10,
        "max_mer": 0.50, "min_yield": 3.5, "min_holdings": 5,
    },
    "education": {
        "equity_pct": 50, "fi_pct": 40, "cash_pct": 10,
        "max_mer": 0.40, "min_yield": 1.5, "min_holdings": 4,
    },
    "preservation": {
        "equity_pct": 20, "fi_pct": 60, "cash_pct": 20,
        "max_mer": 0.30, "min_yield": 2.5, "min_holdings": 3,
    },
}


def _age_adjusted_equity(base_equity: float, age: int | None) -> float:
    """Reduce equity target by ~1% per year over 40. Clamp between 10-95%."""
    if age is None:
        return base_equity
    adjustment = max(0, age - 40) * 1.0
    return max(10, min(95, base_equity - adjustment))


def _score_allocation(actual: dict, benchmark: dict, age: int | None) -> tuple[float, list[str]]:
    """Score allocation fit (0-100). Returns (score, recommendations)."""
    target_eq = _age_adjusted_equity(benchmark["equity_pct"], age)
    target_fi = benchmark["fi_pct"]

    actual_eq = actual.get("Equity", 0)
    actual_fi = actual.get("Fixed Income", 0)

    eq_diff = abs(actual_eq - target_eq)
    fi_diff = abs(actual_fi - target_fi)

    score = max(0, 100 - eq_diff * 1.5 - fi_diff * 1.0)
    recs = []
    if actual_eq > target_eq + 10:
        recs.append(f"Equity allocation ({actual_eq:.0f}%) is above target ({target_eq:.0f}%). Consider shifting to fixed income.")
    elif actual_eq < target_eq - 10:
        recs.append(f"Equity allocation ({actual_eq:.0f}%) is below target ({target_eq:.0f}%). Consider increasing equity exposure.")
    if actual_fi < target_fi - 10:
        recs.append(f"Fixed income ({actual_fi:.0f}%) is below target ({target_fi:.0f}%).")

    return round(score, 1), recs


def _score_fees(weighted_mer: float, max_mer: float) -> tuple[float, list[str]]:
    """Score fee efficiency (0-100)."""
    if weighted_mer <= max_mer:
        score = 100
    else:
        over = weighted_mer - max_mer
        score = max(0, 100 - over * 40)
    recs = []
    if weighted_mer > max_mer:
        recs.append(f"Weighted MER ({weighted_mer:.2f}%) exceeds target ({max_mer:.2f}%). Look for low-cost ETF alternatives.")
    return round(score, 1), recs


def _score_diversification(holding_count: int, sector_count: int, min_holdings: int) -> tuple[float, list[str]]:
    """Score diversification (0-100)."""
    h_score = min(100, (holding_count / max(min_holdings, 1)) * 50)
    s_score = min(50, sector_count * 10)
    score = h_score + s_score
    recs = []
    if holding_count < min_holdings:
        recs.append(f"Only {holding_count} holdings — consider adding more for diversification.")
    if sector_count < 3:
        recs.append(f"Only {sector_count} sectors represented — broaden sector exposure.")
    return round(min(score, 100), 1), recs


def _score_income(weighted_yield: float, min_yield: float) -> tuple[float, list[str]]:
    """Score income generation (0-100)."""
    if weighted_yield >= min_yield:
        score = 100
    else:
        ratio = weighted_yield / max(min_yield, 0.01)
        score = ratio * 100
    recs = []
    if weighted_yield < min_yield:
        recs.append(f"Yield ({weighted_yield:.2f}%) is below target ({min_yield:.2f}%). Consider higher-yield holdings.")
    return round(min(score, 100), 1), recs


def _score_time_horizon(goal_type: str, time_horizon: int | None, actual_equity_pct: float) -> tuple[float, list[str]]:
    """Score time horizon appropriateness (0-100)."""
    if time_horizon is None:
        return 70, ["Provide a time horizon for more accurate scoring."]

    recs = []
    if time_horizon < 5 and actual_equity_pct > 50:
        score = max(0, 100 - (actual_equity_pct - 50) * 2)
        recs.append(f"With only {time_horizon} years, {actual_equity_pct:.0f}% equity is aggressive. Consider de-risking.")
    elif time_horizon > 15 and actual_equity_pct < 40:
        score = max(0, 100 - (40 - actual_equity_pct) * 2)
        recs.append(f"With {time_horizon} years, {actual_equity_pct:.0f}% equity may be too conservative.")
    else:
        score = 90
    return round(min(score, 100), 1), recs


def goal_score(args: dict, state: dict) -> dict:
    """Score portfolio alignment against a financial goal."""
    households = state.get("households", [])
    goal_type = args.get("goal_type", "retirement")
    age = args.get("age")
    time_horizon = args.get("time_horizon_years")
    risk_tolerance = args.get("risk_tolerance")
    target_income = args.get("target_income")

    if not households:
        return {"error": "No portfolio data available. Please upload a brokerage statement first."}

    benchmark = dict(GOAL_BENCHMARKS.get(goal_type, GOAL_BENCHMARKS["retirement"]))

    # Adjust benchmark targets based on risk_tolerance
    if risk_tolerance == "conservative":
        benchmark["equity_pct"] = max(10, benchmark["equity_pct"] - 15)
        benchmark["fi_pct"] = min(80, benchmark["fi_pct"] + 10)
    elif risk_tolerance == "aggressive":
        benchmark["equity_pct"] = min(95, benchmark["equity_pct"] + 15)
        benchmark["fi_pct"] = max(5, benchmark["fi_pct"] - 10)

    # Adjust income target if user specifies target_income
    if target_income and target_income > 0:
        # Will be used in income scoring below
        pass

    # Gather portfolio stats
    total_value = 0
    total_fees = 0
    total_income = 0
    asset_classes: dict[str, float] = {}
    sectors: set[str] = set()
    holding_count = 0

    for h in households:
        for acct in h.get("accounts", []):
            for holding in acct.get("holdings", []):
                val = holding.get("market_value", 0)
                mer = holding.get("mer", 0)
                dy = holding.get("dividend_yield", 0) or 0
                ac = holding.get("asset_class", "Unknown") or "Unknown"
                sec = holding.get("sector", "")

                total_value += val
                total_fees += val * mer / 100
                total_income += val * dy / 100
                asset_classes[ac] = asset_classes.get(ac, 0) + val
                if sec and sec != "Unknown":
                    sectors.add(sec)
                holding_count += 1

    if total_value == 0:
        return {"error": "No holdings with market values found."}

    weighted_mer = total_fees / total_value * 100
    weighted_yield = total_income / total_value * 100
    ac_pct = {k: v / total_value * 100 for k, v in asset_classes.items()}

    # Component scores (weights: allocation 30%, fees 25%, diversification 20%, income 15%, time 10%)
    alloc_score, alloc_recs = _score_allocation(ac_pct, benchmark, age)
    fee_score, fee_recs = _score_fees(weighted_mer, benchmark["max_mer"])
    div_score, div_recs = _score_diversification(holding_count, len(sectors), benchmark["min_holdings"])
    # If user provided target_income, derive required yield and use that
    effective_min_yield = benchmark["min_yield"]
    if target_income and target_income > 0 and total_value > 0:
        required_yield = (target_income / total_value) * 100
        effective_min_yield = max(effective_min_yield, required_yield)
    inc_score, inc_recs = _score_income(weighted_yield, effective_min_yield)
    time_score, time_recs = _score_time_horizon(goal_type, time_horizon, ac_pct.get("Equity", 0))

    composite = round(
        alloc_score * 0.30 + fee_score * 0.25 + div_score * 0.20 + inc_score * 0.15 + time_score * 0.10,
        1,
    )

    all_recs = alloc_recs + fee_recs + div_recs + inc_recs + time_recs

    # Generate widgets
    new_widgets = []

    # Gauge: overall goal alignment
    new_widgets.append({
        "type": "gauge",
        "title": f"Goal Alignment: {goal_type.title()}",
        "data": {
            "value": composite,
            "min": 0,
            "max": 100,
            "label": f"{composite}/100",
            "thresholds": [
                {"value": 40, "color": "#ef4444", "label": "Poor"},
                {"value": 60, "color": "#f59e0b", "label": "Fair"},
                {"value": 80, "color": "#22c55e", "label": "Good"},
                {"value": 100, "color": "#059669", "label": "Excellent"},
            ],
        },
        "confidence": 0.7,
    })

    # Bar: component scores
    new_widgets.append({
        "type": "bar",
        "title": "Goal Score Components",
        "data": [
            {"label": "Allocation (30%)", "value": alloc_score},
            {"label": "Fees (25%)", "value": fee_score},
            {"label": "Diversification (20%)", "value": div_score},
            {"label": "Income (15%)", "value": inc_score},
            {"label": "Time Horizon (10%)", "value": time_score},
        ],
        "confidence": 0.7,
    })

    # Table: recommendations
    if all_recs:
        new_widgets.append({
            "type": "table",
            "title": "Goal Alignment Recommendations",
            "data": {
                "columns": [
                    {"key": "num", "label": "#", "format": "number"},
                    {"key": "recommendation", "label": "Recommendation", "format": "text"},
                ],
                "rows": [{"num": i + 1, "recommendation": r} for i, r in enumerate(all_recs)],
            },
            "gridPosition": {"col": 1, "row": 1, "colSpan": 2},
            "confidence": 0.7,
        })

    return {
        "goal_type": goal_type,
        "composite_score": composite,
        "component_scores": {
            "allocation": alloc_score,
            "fees": fee_score,
            "diversification": div_score,
            "income": inc_score,
            "time_horizon": time_score,
        },
        "portfolio_summary": {
            "total_value": round(total_value, 2),
            "weighted_mer": round(weighted_mer, 3),
            "weighted_yield": round(weighted_yield, 2),
            "holding_count": holding_count,
            "sectors": len(sectors),
        },
        "recommendations": all_recs,
        "new_widgets": new_widgets,
    }
