"""Cross-account duplicate holdings detection."""

DETECT_OVERLAP_SCHEMA = {
    "name": "detect_overlap",
    "description": "Detect duplicate or overlapping holdings across different accounts in the household.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def detect_overlap(args: dict, state: dict) -> dict:
    """Find holdings that appear in multiple accounts."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    # Track symbol → list of (account_name, value)
    symbol_map: dict = {}

    for household in households:
        for account in household.get("accounts", []):
            acct_name = account.get("name", "Unknown")
            for holding in account.get("holdings", []):
                sym = holding.get("symbol", "").upper()
                if not sym:
                    continue
                if sym not in symbol_map:
                    symbol_map[sym] = []
                symbol_map[sym].append({
                    "account": acct_name,
                    "name": holding.get("name", sym),
                    "market_value": holding.get("market_value", 0),
                    "quantity": holding.get("quantity", 0),
                })

    # Filter to symbols in 2+ accounts
    overlaps = {
        sym: entries
        for sym, entries in symbol_map.items()
        if len(entries) > 1
    }

    # Build widgets
    new_widgets = []
    if overlaps:
        rows = []
        for sym, entries in overlaps.items():
            accounts_str = ", ".join(e["account"] for e in entries)
            total = round(sum(e["market_value"] for e in entries), 2)
            rows.append({"symbol": sym, "accounts": accounts_str, "total_value": total, "occurrences": len(entries)})
        rows.sort(key=lambda x: -x["total_value"])
        new_widgets.append({
            "type": "table",
            "title": "Overlapping Holdings Across Accounts",
            "data": {
                "columns": [
                    {"key": "symbol", "label": "Symbol", "format": "text"},
                    {"key": "accounts", "label": "Accounts", "format": "text"},
                    {"key": "total_value", "label": "Combined Value", "format": "currency"},
                    {"key": "occurrences", "label": "Count", "format": "number"},
                ],
                "rows": rows,
            },
            "confidence": 0.8,
        })

    return {
        "overlap_count": len(overlaps),
        "overlaps": {
            sym: {
                "accounts": entries,
                "total_value": round(sum(e["market_value"] for e in entries), 2),
            }
            for sym, entries in overlaps.items()
        },
        "new_widgets": new_widgets,
    }
