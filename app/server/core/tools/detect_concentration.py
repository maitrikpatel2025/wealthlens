"""Concentration risk detection tool."""

DETECT_CONCENTRATION_SCHEMA = {
    "name": "detect_concentration",
    "description": "Detect concentration risk in the portfolio — holdings that represent a disproportionately large share.",
    "parameters": {
        "type": "object",
        "properties": {
            "threshold_percent": {
                "type": "number",
                "description": "Percentage threshold above which a holding is considered concentrated. Default 10.",
            },
        },
        "required": [],
    },
}


def detect_concentration(args: dict, state: dict) -> dict:
    """Find concentrated positions above threshold."""
    households = state.get("households", [])
    threshold = args.get("threshold_percent", 10)

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    # Aggregate by symbol
    totals: dict = {}
    grand_total = 0

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                sym = holding.get("symbol", holding.get("name", "Unknown"))
                val = holding.get("market_value", 0)
                totals[sym] = totals.get(sym, 0) + val
                grand_total += val

    if grand_total == 0:
        return {"error": "No holdings with market values found."}

    concentrated = [
        {
            "symbol": sym,
            "value": round(val, 2),
            "percentage": round(val / grand_total * 100, 2),
        }
        for sym, val in totals.items()
        if (val / grand_total * 100) >= threshold
    ]
    concentrated.sort(key=lambda x: -x["percentage"])

    return {
        "threshold_percent": threshold,
        "total_value": round(grand_total, 2),
        "concentrated_holdings": concentrated,
        "concentrated_count": len(concentrated),
    }
