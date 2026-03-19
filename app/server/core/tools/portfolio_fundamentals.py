"""Portfolio fundamentals: weighted P/E, P/B, P/S, ROE, Debt/Equity vs market averages."""

PORTFOLIO_FUNDAMENTALS_SCHEMA = {
    "name": "portfolio_fundamentals",
    "description": "Compute weighted-average portfolio fundamentals (P/E, P/B, P/S, ROE, Debt/Equity) across equity holdings and compare vs market averages (S&P 500).",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# Market averages (approximate S&P 500 / broad market values)
MARKET_AVERAGES = {
    "P/E Ratio": 22.0,
    "P/B Ratio": 4.5,
    "P/S Ratio": 2.8,
    "ROE (%)": 18.0,
    "Debt/Equity": 120.0,
}


def portfolio_fundamentals(args: dict, state: dict) -> dict:
    """Compute weighted portfolio fundamentals."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    total_value = 0
    equity_value = 0

    # Accumulators: metric_name -> (weighted_sum, weight_sum)
    metrics = {
        "pe_ratio": {"sum": 0, "weight": 0, "label": "P/E Ratio"},
        "price_to_book": {"sum": 0, "weight": 0, "label": "P/B Ratio"},
        "price_to_sales": {"sum": 0, "weight": 0, "label": "P/S Ratio"},
        "roe": {"sum": 0, "weight": 0, "label": "ROE (%)"},
        "debt_to_equity": {"sum": 0, "weight": 0, "label": "Debt/Equity"},
    }

    holdings_with_data = []

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                total_value += val
                asset_class = (holding.get("asset_class", "") or "").lower()

                if asset_class in ("fixed income", "bond", "cash", "money market"):
                    continue
                if val <= 0:
                    continue

                equity_value += val

                holding_data = {"symbol": holding.get("symbol", ""), "name": holding.get("name", ""), "value": val}
                has_data = False

                for field, m in metrics.items():
                    v = holding.get(field)
                    if v is not None and isinstance(v, (int, float)) and v > 0:
                        m["sum"] += v * val
                        m["weight"] += val
                        holding_data[field] = v
                        has_data = True

                if has_data:
                    holdings_with_data.append(holding_data)

    if equity_value == 0:
        return {"error": "No equity holdings found."}

    # Compute weighted averages
    weighted_metrics = {}
    for field, m in metrics.items():
        if m["weight"] > 0:
            weighted_metrics[m["label"]] = round(m["sum"] / m["weight"], 2)
        else:
            weighted_metrics[m["label"]] = None

    # Coverage
    coverage = {}
    for field, m in metrics.items():
        coverage[m["label"]] = round(m["weight"] / equity_value * 100, 1) if equity_value > 0 else 0

    result = {
        "total_equity_value": round(equity_value, 2),
        "weighted_fundamentals": weighted_metrics,
        "data_coverage": coverage,
        "holdings_with_data": len(holdings_with_data),
        "market_averages": MARKET_AVERAGES,
    }

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    # Summary card
    summary_data = []
    for label, val in weighted_metrics.items():
        if val is not None:
            cov = coverage.get(label, 0)
            summary_data.append({"label": label, "value": f"{val:.1f} ({cov:.0f}% cov.)"})
    if summary_data:
        new_widgets.append({
            "type": "summary",
            "title": "Portfolio Fundamentals",
            "data": summary_data,
            "confidence": 0.65,
        })

    # Grouped bar: portfolio vs market averages
    bar_data = []
    for label, val in weighted_metrics.items():
        if val is not None and label in MARKET_AVERAGES:
            bar_data.append({
                "label": label,
                "portfolio": val,
                "market": MARKET_AVERAGES[label],
            })

    if bar_data:
        new_widgets.append({
            "type": "bar",
            "title": "Fundamentals: Portfolio vs Market",
            "data": bar_data,
            "confidence": 0.65,
        })

    result["new_widgets"] = new_widgets
    return result
