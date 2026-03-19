"""Bond analytics: sector, credit quality, maturity breakdown for fixed income holdings."""

BOND_ANALYTICS_SCHEMA = {
    "name": "bond_analytics",
    "description": "Analyze fixed income holdings: bond sector allocation, credit quality distribution, maturity breakdown, and fixed income summary. Works best with Canadian bond ETFs (ZAG, XBB, VAB, ZFL, etc.).",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# Lookup table for well-known Canadian bond ETFs
# Data sourced from ETF fact sheets — approximate compositions
BOND_ETF_DATA = {
    "ZAG": {
        "name": "BMO Aggregate Bond Index ETF",
        "sector": {"Government": 72, "Corporate": 24, "Municipal": 4},
        "credit": {"AAA": 40, "AA": 30, "A": 20, "BBB": 10},
        "maturity": {"0-3Y": 25, "3-7Y": 30, "7-10Y": 20, "10Y+": 25},
        "avg_duration": 7.5,
        "avg_yield": 3.8,
    },
    "XBB": {
        "name": "iShares Core Canadian Universe Bond Index ETF",
        "sector": {"Government": 70, "Corporate": 26, "Municipal": 4},
        "credit": {"AAA": 38, "AA": 32, "A": 20, "BBB": 10},
        "maturity": {"0-3Y": 24, "3-7Y": 28, "7-10Y": 22, "10Y+": 26},
        "avg_duration": 7.8,
        "avg_yield": 3.7,
    },
    "VAB": {
        "name": "Vanguard Canadian Aggregate Bond Index ETF",
        "sector": {"Government": 73, "Corporate": 23, "Municipal": 4},
        "credit": {"AAA": 42, "AA": 28, "A": 20, "BBB": 10},
        "maturity": {"0-3Y": 26, "3-7Y": 29, "7-10Y": 21, "10Y+": 24},
        "avg_duration": 7.4,
        "avg_yield": 3.6,
    },
    "ZFL": {
        "name": "BMO Long Federal Bond Index ETF",
        "sector": {"Government": 100},
        "credit": {"AAA": 100},
        "maturity": {"10Y+": 100},
        "avg_duration": 17.0,
        "avg_yield": 3.2,
    },
    "XLB": {
        "name": "iShares Core Canadian Long Term Bond Index ETF",
        "sector": {"Government": 65, "Corporate": 30, "Municipal": 5},
        "credit": {"AAA": 35, "AA": 25, "A": 25, "BBB": 15},
        "maturity": {"10Y+": 100},
        "avg_duration": 14.5,
        "avg_yield": 4.0,
    },
    "ZDB": {
        "name": "BMO Discount Bond Index ETF",
        "sector": {"Government": 60, "Corporate": 35, "Municipal": 5},
        "credit": {"AAA": 30, "AA": 25, "A": 28, "BBB": 17},
        "maturity": {"0-3Y": 30, "3-7Y": 35, "7-10Y": 20, "10Y+": 15},
        "avg_duration": 5.5,
        "avg_yield": 3.5,
    },
    "CLF": {
        "name": "iShares 1-5 Year Laddered Corporate Bond Index ETF",
        "sector": {"Corporate": 100},
        "credit": {"AA": 15, "A": 45, "BBB": 40},
        "maturity": {"0-3Y": 40, "3-7Y": 60},
        "avg_duration": 2.8,
        "avg_yield": 4.2,
    },
    "VSB": {
        "name": "Vanguard Canadian Short-Term Bond Index ETF",
        "sector": {"Government": 70, "Corporate": 25, "Municipal": 5},
        "credit": {"AAA": 45, "AA": 25, "A": 20, "BBB": 10},
        "maturity": {"0-3Y": 60, "3-7Y": 40},
        "avg_duration": 2.7,
        "avg_yield": 3.9,
    },
    "ZCS": {
        "name": "BMO Short Corporate Bond Index ETF",
        "sector": {"Corporate": 100},
        "credit": {"AA": 10, "A": 45, "BBB": 45},
        "maturity": {"0-3Y": 50, "3-7Y": 50},
        "avg_duration": 2.9,
        "avg_yield": 4.5,
    },
    "XSB": {
        "name": "iShares Core Canadian Short Term Bond Index ETF",
        "sector": {"Government": 65, "Corporate": 30, "Municipal": 5},
        "credit": {"AAA": 40, "AA": 25, "A": 22, "BBB": 13},
        "maturity": {"0-3Y": 65, "3-7Y": 35},
        "avg_duration": 2.6,
        "avg_yield": 3.8,
    },
    "ZHY": {
        "name": "BMO High Yield US Corporate Bond Hedged to CAD ETF",
        "sector": {"Corporate": 100},
        "credit": {"BB": 50, "B": 35, "CCC": 15},
        "maturity": {"0-3Y": 15, "3-7Y": 50, "7-10Y": 25, "10Y+": 10},
        "avg_duration": 4.2,
        "avg_yield": 7.5,
    },
    "XHY": {
        "name": "iShares US High Yield Bond Index ETF (CAD-Hedged)",
        "sector": {"Corporate": 100},
        "credit": {"BB": 48, "B": 37, "CCC": 15},
        "maturity": {"0-3Y": 12, "3-7Y": 52, "7-10Y": 26, "10Y+": 10},
        "avg_duration": 4.0,
        "avg_yield": 7.2,
    },
}

# Keywords to detect fixed income assets not in lookup table
BOND_KEYWORDS = ("bond", "fixed income", "aggregate", "treasury", "government", "corporate bond", "high yield")

# Default breakdown for unknown bond ETFs (approximate broad market bond)
_DEFAULT_BOND_DATA = {
    "sector": {"Government": 60, "Corporate": 35, "Municipal": 5},
    "credit": {"AAA": 30, "AA": 25, "A": 25, "BBB": 20},
    "maturity": {"0-3Y": 25, "3-7Y": 30, "7-10Y": 25, "10Y+": 20},
    "avg_duration": 6.0,
    "avg_yield": 3.5,
}


def _fetch_bond_data_yfinance(symbol: str) -> dict | None:
    """Try to get basic bond fund metrics from yfinance for ETFs not in the lookup table."""
    try:
        import yfinance as yf
        suffix = f"{symbol}.TO" if "." not in symbol else symbol
        info = yf.Ticker(suffix).info or {}
        if not info.get("regularMarketPrice"):
            info = yf.Ticker(symbol).info or {}
        if not info:
            return None

        data = dict(_DEFAULT_BOND_DATA)
        # Override yield if available
        div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
        if div_yield and isinstance(div_yield, (int, float)) and div_yield > 0:
            data["avg_yield"] = round(float(div_yield) * 100, 2)
        data["name"] = info.get("longName", info.get("shortName", symbol))
        return data
    except Exception:
        return None


def bond_analytics(args: dict, state: dict) -> dict:
    """Analyze fixed income portion of portfolio."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    total_portfolio_value = 0
    total_fi_value = 0
    fi_holdings = []

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                total_portfolio_value += val
                sym = (holding.get("symbol", "") or "").upper().replace(".TO", "")
                name = (holding.get("name", "") or "").lower()
                asset_class = (holding.get("asset_class", "") or "").lower()

                is_bond = (
                    sym in BOND_ETF_DATA
                    or asset_class in ("fixed income", "bond")
                    or any(kw in name for kw in BOND_KEYWORDS)
                )

                if is_bond and val > 0:
                    total_fi_value += val
                    etf_data = BOND_ETF_DATA.get(sym)
                    if etf_data is None:
                        # Try yfinance fallback for unlisted bond ETFs
                        etf_data = _fetch_bond_data_yfinance(sym)
                    fi_holdings.append({
                        "symbol": sym,
                        "name": holding.get("name", sym),
                        "market_value": val,
                        "data": etf_data,
                    })

    if not fi_holdings:
        return {
            "error": "No fixed income holdings detected in the portfolio.",
            "total_portfolio_value": round(total_portfolio_value, 2),
        }

    fi_pct = (total_fi_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0

    # Weighted aggregation of sector, credit, maturity
    sector_agg = {}
    credit_agg = {}
    maturity_agg = {}
    weighted_duration = 0
    weighted_yield = 0
    known_value = 0

    for h in fi_holdings:
        val = h["market_value"]
        data = h["data"]
        if data:
            known_value += val
            weight = val / total_fi_value if total_fi_value > 0 else 0

            for k, v in data.get("sector", {}).items():
                sector_agg[k] = sector_agg.get(k, 0) + v * weight

            for k, v in data.get("credit", {}).items():
                credit_agg[k] = credit_agg.get(k, 0) + v * weight

            for k, v in data.get("maturity", {}).items():
                maturity_agg[k] = maturity_agg.get(k, 0) + v * weight

            weighted_duration += data.get("avg_duration", 0) * weight
            weighted_yield += data.get("avg_yield", 0) * weight

    def to_breakdown(agg: dict) -> list:
        total = sum(agg.values())
        if total == 0:
            return []
        return sorted(
            [{"name": k, "value": round(v, 1), "percentage": round(v, 1)} for k, v in agg.items()],
            key=lambda x: -x["percentage"]
        )

    sector_breakdown = to_breakdown(sector_agg)
    credit_breakdown = to_breakdown(credit_agg)
    maturity_breakdown = to_breakdown(maturity_agg)

    result = {
        "total_portfolio_value": round(total_portfolio_value, 2),
        "total_fixed_income_value": round(total_fi_value, 2),
        "fixed_income_pct": round(fi_pct, 1),
        "holdings_count": len(fi_holdings),
        "known_etf_coverage_pct": round(known_value / total_fi_value * 100, 1) if total_fi_value > 0 else 0,
        "weighted_avg_duration": round(weighted_duration, 1),
        "weighted_avg_yield": round(weighted_yield, 2),
        "sector_breakdown": sector_breakdown,
        "credit_quality": credit_breakdown,
        "maturity_breakdown": maturity_breakdown,
        "holdings": [{"symbol": h["symbol"], "name": h["name"], "value": round(h["market_value"], 2)} for h in fi_holdings],
    }

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    # Fixed income summary
    new_widgets.append({
        "type": "summary",
        "title": "Fixed Income Summary",
        "data": [
            {"label": "FI Allocation", "value": f"{fi_pct:.1f}%"},
            {"label": "FI Value", "value": f"${total_fi_value:,.0f}"},
            {"label": "Avg Duration", "value": f"{weighted_duration:.1f} yrs"},
            {"label": "Avg Yield", "value": f"{weighted_yield:.2f}%"},
        ],
        "confidence": 0.7,
    })

    if sector_breakdown:
        new_widgets.append({
            "type": "pie",
            "title": "Bond Sector Allocation",
            "data": [{"name": s["name"], "value": s["percentage"]} for s in sector_breakdown],
            "confidence": 0.7,
        })

    if credit_breakdown:
        new_widgets.append({
            "type": "pie",
            "title": "Credit Quality Distribution",
            "data": [{"name": c["name"], "value": c["percentage"]} for c in credit_breakdown],
            "confidence": 0.7,
        })

    if maturity_breakdown:
        new_widgets.append({
            "type": "pie",
            "title": "Maturity Profile",
            "data": [{"name": m["name"], "value": m["percentage"]} for m in maturity_breakdown],
            "confidence": 0.7,
        })

    result["new_widgets"] = new_widgets
    return result
