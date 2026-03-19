"""Shared utility: filter holdings before analysis."""

import copy
from typing import Any


def apply_holding_filter(households: list[dict], filter_args: dict | None) -> list[dict]:
    """
    Deep-copy households and keep only holdings matching the filter criteria.

    Supported filter keys:
      symbols:      list[str]  — only keep these ticker symbols
      account_type: str        — e.g. "TFSA", "RRSP"
      asset_class:  str        — e.g. "Equity", "Fixed Income"
      sector:       str        — e.g. "Technology"
      country:      str        — e.g. "Canada"
      min_value:    float      — minimum market_value

    Returns a new households list (deep-copied, never mutates the original).
    If filter_args is None or empty, returns the original list unchanged.
    """
    if not filter_args:
        return households

    filtered = copy.deepcopy(households)

    symbols = [s.upper() for s in filter_args.get("symbols", [])] if filter_args.get("symbols") else None
    account_type = (filter_args.get("account_type") or "").strip()
    asset_class = (filter_args.get("asset_class") or "").strip().lower()
    sector = (filter_args.get("sector") or "").strip().lower()
    country = (filter_args.get("country") or "").strip().lower()
    min_value = filter_args.get("min_value", 0) or 0

    for household in filtered:
        kept_accounts = []
        for account in household.get("accounts", []):
            # Account-level filter
            if account_type:
                acct = (account.get("type") or account.get("name") or "").strip()
                if acct.lower() != account_type.lower():
                    continue

            kept_holdings = []
            for h in account.get("holdings", []):
                if symbols and (h.get("symbol", "").upper() not in symbols):
                    continue
                if asset_class and (h.get("asset_class", "") or "").lower() != asset_class:
                    continue
                if sector and (h.get("sector", "") or "").lower() != sector:
                    continue
                if country and (h.get("country", "") or "").lower() != country:
                    continue
                if h.get("market_value", 0) < min_value:
                    continue
                kept_holdings.append(h)

            if kept_holdings:
                account["holdings"] = kept_holdings
                account["total_value"] = round(sum(h.get("market_value", 0) for h in kept_holdings), 2)
                kept_accounts.append(account)

        household["accounts"] = kept_accounts

    return filtered


# JSON schema fragment to embed in tool schemas
FILTER_SCHEMA_PROPERTIES: dict[str, Any] = {
    "filter": {
        "type": "object",
        "description": "Optional filter to narrow the analysis to a subset of holdings.",
        "properties": {
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Only analyse these ticker symbols.",
            },
            "account_type": {
                "type": "string",
                "description": "Only include holdings in this account type (e.g. TFSA, RRSP).",
            },
            "asset_class": {
                "type": "string",
                "description": "Only include holdings with this asset class (e.g. Equity, Fixed Income).",
            },
            "sector": {
                "type": "string",
                "description": "Only include holdings in this sector.",
            },
            "country": {
                "type": "string",
                "description": "Only include holdings domiciled in this country.",
            },
            "min_value": {
                "type": "number",
                "description": "Only include holdings with market value >= this amount.",
            },
        },
        "required": [],
    },
}
