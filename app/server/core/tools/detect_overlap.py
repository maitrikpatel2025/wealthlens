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

    return {
        "overlap_count": len(overlaps),
        "overlaps": {
            sym: {
                "accounts": entries,
                "total_value": round(sum(e["market_value"] for e in entries), 2),
            }
            for sym, entries in overlaps.items()
        },
    }
