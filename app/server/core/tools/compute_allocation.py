"""Asset allocation breakdown tool."""

COMPUTE_ALLOCATION_SCHEMA = {
    "name": "compute_allocation",
    "description": "Compute asset allocation breakdown across all accounts. Returns allocation by asset class, sector, geography/country, market cap, currency, or account type.",
    "parameters": {
        "type": "object",
        "properties": {
            "group_by": {
                "type": "string",
                "enum": ["asset_class", "sector", "country", "market_cap_class", "currency", "account_type", "geographic_exposure"],
                "description": "How to group the allocation breakdown. 'country' = domicile country, 'geographic_exposure' = where the fund actually invests (e.g., VFV invests in US despite being Canadian-domiciled).",
            },
        },
        "required": [],
    },
}

# Legacy field mapping for backward compatibility
FIELD_ALIASES = {
    "geography": "country",
    "geo": "geographic_exposure",
    "cap": "market_cap_class",
    "market_cap": "market_cap_class",
}


def compute_allocation(args: dict, state: dict) -> dict:
    """Compute allocation from household holdings."""
    households = state.get("households", [])
    group_by = args.get("group_by", "asset_class")

    # Resolve aliases
    group_by = FIELD_ALIASES.get(group_by, group_by)

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    # Aggregate holdings across all accounts
    totals = {}
    grand_total = 0

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                value = holding.get("market_value", 0)

                # Special handling for account_type — comes from account, not holding
                if group_by == "account_type":
                    key = account.get("type", account.get("name", "Unknown"))
                else:
                    key = holding.get(group_by, "Unknown")

                # Clean up empty/None keys
                if not key or key == "None":
                    key = "Unknown"

                totals[key] = totals.get(key, 0) + value
                grand_total += value

    if grand_total == 0:
        return {"error": "No holdings with market values found."}

    allocation = [
        {
            "name": k,
            "value": round(v, 2),
            "percentage": round(v / grand_total * 100, 2),
        }
        for k, v in sorted(totals.items(), key=lambda x: -x[1])
    ]

    # --- Auto-generate dashboard widget ---
    group_labels = {
        "asset_class": "Asset Class",
        "sector": "Sector",
        "country": "Country",
        "market_cap_class": "Market Cap",
        "currency": "Currency",
        "account_type": "Account Type",
        "geographic_exposure": "Geographic Exposure",
    }
    widget_title = f"Allocation by {group_labels.get(group_by, group_by)}"
    new_widgets = [{
        "type": "pie",
        "title": widget_title,
        "data": [{"name": a["name"], "value": a["percentage"]} for a in allocation],
        "confidence": 0.85,
    }]

    return {
        "group_by": group_by,
        "total_value": round(grand_total, 2),
        "allocation": allocation,
        "new_widgets": new_widgets,
    }
