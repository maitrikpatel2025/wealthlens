"""Auto-generate starter dashboard widgets from enriched extraction results."""

import uuid

AUTO_DASHBOARD_SCHEMA = {
    "name": "auto_dashboard",
    "description": "Automatically generate a starter dashboard with widgets from the latest statement extraction results.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def auto_dashboard(args: dict, state: dict) -> dict:
    """Generate starter widgets from extraction results."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data. Upload a statement first.", "widgets": []}

    # Collect all holdings
    all_holdings = []
    account_values = {}
    for household in households:
        for account in household.get("accounts", []):
            acct_name = account.get("name", "Unknown")
            acct_type = account.get("type", "Unknown")
            acct_total = 0
            for holding in account.get("holdings", []):
                holding["account_name"] = acct_name
                holding["account_type_resolved"] = acct_type
                all_holdings.append(holding)
                acct_total += holding.get("market_value", 0)
            account_values[acct_name] = acct_total

    if not all_holdings:
        return {"error": "No holdings found.", "widgets": []}

    widgets = []

    # -- 1. Portfolio Overview summary --
    total_value = round(sum(h.get("market_value", 0) for h in all_holdings), 2)
    total_book = round(sum(h.get("book_cost", 0) or 0 for h in all_holdings), 2)
    total_gain = round(total_value - total_book, 2) if total_book > 0 else None

    summary_items = [
        {"label": "Total Value", "value": total_value, "format": "currency"},
        {"label": "Holdings", "value": len(all_holdings), "format": "number"},
        {"label": "Accounts", "value": len(account_values), "format": "number"},
    ]
    if total_gain is not None:
        summary_items.append({
            "label": "Unrealized Gain",
            "value": total_gain,
            "format": "currency",
            "trend": "up" if total_gain > 0 else "down",
        })

    widgets.append({
        "id": f"w-{uuid.uuid4().hex[:8]}",
        "type": "summary",
        "title": "Portfolio Overview",
        "data": summary_items,
        "confidence": 0.95,
    })

    # -- 2. Account type allocation pie --
    acct_type_values = {}
    for h in all_holdings:
        at = h.get("account_type", h.get("account_type_resolved", "Unknown")) or "Unknown"
        acct_type_values[at] = acct_type_values.get(at, 0) + h.get("market_value", 0)
    if acct_type_values:
        widgets.append({
            "id": f"w-{uuid.uuid4().hex[:8]}",
            "type": "pie",
            "title": "Allocation by Account Type",
            "data": [{"name": k, "value": round(v, 2)} for k, v in sorted(acct_type_values.items(), key=lambda x: -x[1])],
            "confidence": 0.95,
        })

    # -- 3. Asset class allocation pie (from enrichment) --
    asset_classes = {}
    for h in all_holdings:
        ac = h.get("asset_class", "Unknown") or "Unknown"
        asset_classes[ac] = asset_classes.get(ac, 0) + h.get("market_value", 0)
    # Only show if we have meaningful data (not all "Unknown")
    if asset_classes and not (len(asset_classes) == 1 and "Unknown" in asset_classes):
        widgets.append({
            "id": f"w-{uuid.uuid4().hex[:8]}",
            "type": "pie",
            "title": "Asset Class Breakdown",
            "data": [{"name": k, "value": round(v, 2)} for k, v in sorted(asset_classes.items(), key=lambda x: -x[1])],
            "confidence": 0.85,
        })

    # -- 4. Top holdings bar chart --
    top_holdings = sorted(all_holdings, key=lambda h: -h.get("market_value", 0))[:10]
    if top_holdings:
        widgets.append({
            "id": f"w-{uuid.uuid4().hex[:8]}",
            "type": "bar",
            "title": "Top Holdings by Value",
            "data": [
                {"label": h.get("symbol", h.get("name", "?"))[:12], "value": round(h.get("market_value", 0), 2)}
                for h in top_holdings
            ],
            "confidence": 0.95,
        })

    # -- 5. Holdings table with enriched data --
    columns = [
        {"key": "symbol", "label": "Symbol", "format": "text"},
        {"key": "name", "label": "Name", "format": "text"},
        {"key": "quantity", "label": "Qty", "format": "number"},
        {"key": "market_value", "label": "Value", "format": "currency"},
        {"key": "current_price", "label": "Price", "format": "currency"},
        {"key": "account", "label": "Account", "format": "text"},
        {"key": "asset_class", "label": "Type", "format": "text"},
    ]

    rows = []
    for h in all_holdings:
        row = {
            "symbol": h.get("symbol", ""),
            "name": h.get("name", ""),
            "quantity": h.get("quantity", 0),
            "market_value": round(h.get("market_value", 0), 2),
            "current_price": h.get("current_price", ""),
            "account": h.get("account_type", h.get("account_name", "")),
            "asset_class": h.get("asset_class", ""),
        }
        rows.append(row)

    widgets.append({
        "id": f"w-{uuid.uuid4().hex[:8]}",
        "type": "table",
        "title": "All Holdings",
        "data": {"columns": columns, "rows": rows},
        "confidence": 0.9,
        "gridPosition": {"col": 1, "row": 4, "colSpan": 2},
    })

    # -- 6. Fee impact (if MER data available) --
    mer_holdings = [h for h in all_holdings if h.get("mer") and h.get("mer", 0) > 0]
    if mer_holdings:
        widgets.append({
            "id": f"w-{uuid.uuid4().hex[:8]}",
            "type": "bar",
            "title": "Annual Fee Impact ($)",
            "data": [
                {
                    "label": h.get("symbol", h.get("name", "?"))[:12],
                    "value": round(h.get("market_value", 0) * h.get("mer", 0) / 100, 2),
                }
                for h in sorted(mer_holdings, key=lambda x: -x.get("market_value", 0) * x.get("mer", 0) / 100)[:10]
            ],
            "confidence": 0.85,
        })

    # -- 7. Gain/Loss bar chart --
    gain_loss_holdings = [h for h in all_holdings if h.get("book_cost") and h.get("book_cost", 0) > 0]
    if gain_loss_holdings:
        widgets.append({
            "id": f"w-{uuid.uuid4().hex[:8]}",
            "type": "bar",
            "title": "Unrealized Gain/Loss by Holding",
            "data": [
                {
                    "label": h.get("symbol", h.get("name", "?"))[:12],
                    "value": round(h.get("market_value", 0) - h.get("book_cost", 0), 2),
                }
                for h in sorted(
                    gain_loss_holdings,
                    key=lambda x: -(x.get("market_value", 0) - x.get("book_cost", 0)),
                )[:10]
            ],
            "confidence": 0.9,
        })

    return {"widgets": widgets, "count": len(widgets)}
