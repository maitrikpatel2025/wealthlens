"""Stock style box analysis: Size (Large/Mid/Small) x Style (Value/Blend/Growth)."""

STOCK_STYLE_ANALYSIS_SCHEMA = {
    "name": "stock_style_analysis",
    "description": "Morningstar-style 3x3 stock style box analysis. Classifies equity holdings by size (Large/Mid/Small Cap) and style (Value/Blend/Growth) based on market cap, P/E, and P/B ratios.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

SIZE_LABELS = ["Large Cap", "Mid Cap", "Small Cap"]
STYLE_LABELS = ["Value", "Blend", "Growth"]


def stock_style_analysis(args: dict, state: dict) -> dict:
    """Classify equity holdings into a 3x3 style box."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    total_value = 0
    equity_value = 0

    # Style box grid: rows = size, cols = style
    grid = {}
    for size in SIZE_LABELS:
        for style in STYLE_LABELS:
            grid[f"{size}|{style}"] = 0.0

    holdings_classified = []

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                total_value += val
                asset_class = (holding.get("asset_class", "") or "").lower()

                # Only classify equity and equity-like holdings
                if asset_class in ("fixed income", "bond", "cash", "money market"):
                    continue
                if val <= 0:
                    continue

                equity_value += val

                size = holding.get("market_cap_class", "") or "Large Cap"
                if size not in SIZE_LABELS:
                    size = "Large Cap"

                style = holding.get("style_class", "") or "Blend"
                if style not in STYLE_LABELS:
                    style = "Blend"

                key = f"{size}|{style}"
                grid[key] += val

                holdings_classified.append({
                    "symbol": holding.get("symbol", ""),
                    "name": holding.get("name", ""),
                    "size": size,
                    "style": style,
                    "value": round(val, 2),
                })

    if equity_value == 0:
        return {"error": "No equity holdings to classify."}

    # Convert grid to percentages
    grid_pct = {}
    for key, val in grid.items():
        grid_pct[key] = round(val / equity_value * 100, 1) if equity_value > 0 else 0

    # Build style box table data
    table_rows = []
    for size in SIZE_LABELS:
        row = {"size": size}
        for style in STYLE_LABELS:
            key = f"{size}|{style}"
            row[style.lower()] = f"{grid_pct[key]:.1f}%"
        table_rows.append(row)

    # Summary: dominant style
    max_key = max(grid_pct, key=grid_pct.get)
    dominant_size, dominant_style = max_key.split("|")

    result = {
        "total_equity_value": round(equity_value, 2),
        "equity_pct_of_portfolio": round(equity_value / total_value * 100, 1) if total_value > 0 else 0,
        "dominant_size": dominant_size,
        "dominant_style": dominant_style,
        "style_grid": grid_pct,
        "holdings_classified": len(holdings_classified),
        "holdings": holdings_classified[:20],
    }

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    # Style box as table
    new_widgets.append({
        "type": "table",
        "title": "Equity Style Box",
        "data": {
            "columns": [
                {"key": "size", "label": "Size", "format": "text"},
                {"key": "value", "label": "Value", "format": "text"},
                {"key": "blend", "label": "Blend", "format": "text"},
                {"key": "growth", "label": "Growth", "format": "text"},
            ],
            "rows": table_rows,
        },
        "confidence": 0.65,
    })

    # Summary
    new_widgets.append({
        "type": "summary",
        "title": "Style Analysis Summary",
        "data": [
            {"label": "Dominant Size", "value": dominant_size},
            {"label": "Dominant Style", "value": dominant_style},
            {"label": "Equity Value", "value": f"${equity_value:,.0f}"},
            {"label": "Holdings Classified", "value": str(len(holdings_classified))},
        ],
        "confidence": 0.65,
    })

    result["new_widgets"] = new_widgets
    return result
