"""MER/fee analysis tool with low-cost alternative suggestions."""

from core.tools.filter_utils import FILTER_SCHEMA_PROPERTIES

COMPUTE_FEES_SCHEMA = {
    "name": "compute_fees",
    "description": "Analyze management expense ratios (MERs) and trading fees across holdings. Returns fee breakdown by fund. Set show_alternatives=true to flag high-cost holdings and suggest lower-cost ETF alternatives. Supports optional filter to narrow analysis.",
    "parameters": {
        "type": "object",
        "properties": {
            "show_alternatives": {
                "type": "boolean",
                "description": "When true, flag holdings with MER > 0.50% and suggest lower-cost ETF alternatives with estimated 10-year savings.",
            },
            **FILTER_SCHEMA_PROPERTIES,
        },
        "required": [],
    },
}

# Low-cost ETF alternatives by category
# Maps asset class / sector keywords to suggested low-cost ETFs
LOW_COST_ALTERNATIVES = {
    # Canadian equity
    "canadian equity": {"symbol": "XIC.TO", "name": "iShares Core S&P/TSX Capped Composite", "mer": 0.06},
    "tsx": {"symbol": "XIC.TO", "name": "iShares Core S&P/TSX Capped Composite", "mer": 0.06},
    "s&p/tsx": {"symbol": "XIC.TO", "name": "iShares Core S&P/TSX Capped Composite", "mer": 0.06},
    # US equity
    "us equity": {"symbol": "VFV.TO", "name": "Vanguard S&P 500 Index ETF", "mer": 0.09},
    "s&p 500": {"symbol": "VFV.TO", "name": "Vanguard S&P 500 Index ETF", "mer": 0.09},
    "american": {"symbol": "VFV.TO", "name": "Vanguard S&P 500 Index ETF", "mer": 0.09},
    # International equity
    "international": {"symbol": "XEF.TO", "name": "iShares Core MSCI EAFE", "mer": 0.22},
    "eafe": {"symbol": "XEF.TO", "name": "iShares Core MSCI EAFE", "mer": 0.22},
    "global equity": {"symbol": "XEQT.TO", "name": "iShares Core Equity ETF Portfolio", "mer": 0.20},
    # Bonds
    "bond": {"symbol": "ZAG.TO", "name": "BMO Aggregate Bond Index ETF", "mer": 0.09},
    "fixed income": {"symbol": "ZAG.TO", "name": "BMO Aggregate Bond Index ETF", "mer": 0.09},
    # Balanced
    "balanced": {"symbol": "VBAL.TO", "name": "Vanguard Balanced ETF Portfolio", "mer": 0.24},
    "growth": {"symbol": "VGRO.TO", "name": "Vanguard Growth ETF Portfolio", "mer": 0.24},
    # Dividend
    "dividend": {"symbol": "VDY.TO", "name": "Vanguard FTSE Canadian High Dividend Yield", "mer": 0.22},
    # Default catch-all for equity mutual funds
    "equity": {"symbol": "XEQT.TO", "name": "iShares Core Equity ETF Portfolio", "mer": 0.20},
}

# MER threshold for flagging high-cost holdings
HIGH_COST_THRESHOLD = 0.50  # 0.50%


def _find_alternative(holding: dict) -> dict | None:
    """Find a lower-cost ETF alternative based on fund name and asset class."""
    name = (holding.get("name", "") or "").lower()
    asset_class = (holding.get("asset_class", "") or "").lower()
    sector = (holding.get("sector", "") or "").lower()
    geo = (holding.get("geographic_exposure", "") or "").lower()

    # Try matching on fund name keywords
    search_text = f"{name} {asset_class} {sector} {geo}"

    for keyword, alt in LOW_COST_ALTERNATIVES.items():
        if keyword in search_text:
            return alt

    # Default: if it's a mutual fund, suggest broad equity ETF
    if "mutual fund" in asset_class:
        return LOW_COST_ALTERNATIVES["equity"]

    return None


def compute_fees(args: dict, state: dict) -> dict:
    """Compute fee analysis from household holdings."""
    from core.tools.filter_utils import apply_holding_filter
    households = apply_holding_filter(state.get("households", []), args.get("filter"))
    show_alternatives = args.get("show_alternatives", False)

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    fee_breakdown = []
    total_fees = 0
    total_value = 0

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                value = holding.get("market_value", 0)
                mer = holding.get("mer", 0)
                annual_fee = value * mer / 100
                total_fees += annual_fee
                total_value += value

                if mer > 0:
                    item = {
                        "name": holding.get("name", holding.get("symbol", "Unknown")),
                        "symbol": holding.get("symbol", ""),
                        "market_value": round(value, 2),
                        "mer_percent": mer,
                        "annual_fee": round(annual_fee, 2),
                        "account": account.get("name", "Unknown"),
                    }
                    # Enhanced fee fields (Phase 5)
                    ger = holding.get("gross_expense_ratio")
                    if ger and isinstance(ger, (int, float)) and ger > 0:
                        item["gross_expense_ratio"] = ger
                    fl = holding.get("front_load")
                    if fl and isinstance(fl, (int, float)) and fl > 0:
                        item["front_load"] = fl
                    dl = holding.get("deferred_load")
                    if dl and isinstance(dl, (int, float)) and dl > 0:
                        item["deferred_load"] = dl
                    fee_breakdown.append(item)

    fee_breakdown.sort(key=lambda x: -x["annual_fee"])
    weighted_mer = (total_fees / total_value * 100) if total_value > 0 else 0

    result = {
        "total_value": round(total_value, 2),
        "total_annual_fees": round(total_fees, 2),
        "weighted_avg_mer": round(weighted_mer, 3),
        "fee_breakdown": fee_breakdown,
    }

    # Show alternatives: flag high-cost holdings and compute savings
    if show_alternatives:
        high_cost_flags = []
        total_potential_savings = 0

        for item in fee_breakdown:
            if item["mer_percent"] > HIGH_COST_THRESHOLD:
                holding_data = {"name": item["name"], "asset_class": "", "sector": "",
                                "geographic_exposure": ""}
                # Find the original holding to get metadata
                for household in households:
                    for account in household.get("accounts", []):
                        for h in account.get("holdings", []):
                            if h.get("symbol", "") == item["symbol"]:
                                holding_data = h
                                break

                alt = _find_alternative(holding_data)

                current_annual = item["annual_fee"]
                flag = {
                    "name": item["name"],
                    "symbol": item["symbol"],
                    "current_mer": item["mer_percent"],
                    "annual_fee": current_annual,
                    "market_value": item["market_value"],
                }

                if alt:
                    alt_annual = item["market_value"] * alt["mer"] / 100
                    annual_savings = current_annual - alt_annual
                    # 10-year compounding fee drag: approximate as value * (mer_diff/100) * 10
                    # with simple compound growth assumption of 6% annual return
                    mer_diff = item["mer_percent"] - alt["mer"]
                    ten_year_drag = _compute_fee_drag(item["market_value"], mer_diff / 100, 10, 0.06)

                    flag["suggested_alternative"] = {
                        "symbol": alt["symbol"],
                        "name": alt["name"],
                        "mer": alt["mer"],
                    }
                    flag["annual_savings"] = round(annual_savings, 2)
                    flag["ten_year_fee_drag"] = round(ten_year_drag, 2)
                    total_potential_savings += annual_savings

                high_cost_flags.append(flag)

        result["high_cost_flags"] = high_cost_flags
        result["total_potential_annual_savings"] = round(total_potential_savings, 2)
        result["high_cost_threshold"] = HIGH_COST_THRESHOLD

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    if fee_breakdown:
        new_widgets.append({
            "type": "bar",
            "title": "MER by Holding (%)",
            "data": [{"label": f["symbol"] or f["name"], "value": f["mer_percent"]} for f in fee_breakdown[:10]],
            "confidence": 0.85,
        })

    # Enhanced fee detail table if any holdings have gross_expense_ratio or load fees
    has_enhanced = any(f.get("gross_expense_ratio") or f.get("front_load") or f.get("deferred_load") for f in fee_breakdown)
    if has_enhanced:
        fee_table_cols = [
            {"key": "symbol", "label": "Symbol", "format": "text"},
            {"key": "name", "label": "Name", "format": "text"},
            {"key": "mer_percent", "label": "Net MER %", "format": "percent"},
            {"key": "gross_expense_ratio", "label": "Gross ER %", "format": "percent"},
            {"key": "front_load", "label": "Front Load %", "format": "percent"},
            {"key": "deferred_load", "label": "Deferred Load %", "format": "percent"},
            {"key": "annual_fee", "label": "Annual Fee", "format": "currency"},
        ]
        fee_table_rows = []
        for f in fee_breakdown[:15]:
            fee_table_rows.append({
                "symbol": f.get("symbol", ""),
                "name": f.get("name", "")[:25],
                "mer_percent": f["mer_percent"],
                "gross_expense_ratio": f.get("gross_expense_ratio", "—"),
                "front_load": f.get("front_load", "—"),
                "deferred_load": f.get("deferred_load", "—"),
                "annual_fee": f["annual_fee"],
            })
        new_widgets.append({
            "type": "table",
            "title": "Detailed Fee Breakdown",
            "data": {"columns": fee_table_cols, "rows": fee_table_rows},
            "gridPosition": {"col": 1, "row": 1, "colSpan": 2},
            "confidence": 0.8,
        })

    if show_alternatives and result.get("high_cost_flags"):
        comparison_data = []
        for flag in result["high_cost_flags"]:
            item = {"label": flag["symbol"] or flag["name"], "current": flag["current_mer"]}
            if "suggested_alternative" in flag:
                item["alternative"] = flag["suggested_alternative"]["mer"]
            comparison_data.append(item)
        if comparison_data:
            new_widgets.append({
                "type": "bar",
                "title": "Fee Comparison: Current vs Low-Cost Alternative",
                "data": comparison_data,
                "confidence": 0.8,
            })

    result["new_widgets"] = new_widgets
    return result


def _compute_fee_drag(value: float, fee_diff: float, years: int, annual_return: float) -> float:
    """
    Compute the compounding fee drag over N years.
    Returns the dollar difference between investing at (return) vs (return - fee_diff).
    """
    if fee_diff <= 0 or value <= 0:
        return 0.0

    # Growth without extra fees
    growth_low_fee = value * ((1 + annual_return) ** years)
    # Growth with higher fees (reduced return)
    growth_high_fee = value * ((1 + annual_return - fee_diff) ** years)

    return growth_low_fee - growth_high_fee
