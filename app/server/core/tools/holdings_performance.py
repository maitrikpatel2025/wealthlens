"""Per-holding annualized performance: 1Y, 3Y, 5Y, 10Y, All-Time returns."""

try:
    import yfinance as yf
except ImportError:
    yf = None

HOLDINGS_PERFORMANCE_SCHEMA = {
    "name": "holdings_performance",
    "description": "Show annualized 1Y/3Y/5Y/10Y/All-Time returns for each holding in the portfolio. Displays a full-width performance table.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

PERIODS = {
    "1Y": 365,
    "3Y": 365 * 3,
    "5Y": 365 * 5,
    "10Y": 365 * 10,
}


def _ensure_to(symbol: str) -> str:
    upper = symbol.upper()
    if "." in upper:
        return upper
    return f"{upper}.TO"


def _annualized_return(start_price: float, end_price: float, years: float) -> float:
    """Compute annualized return: (end/start)^(1/years) - 1."""
    if start_price <= 0 or end_price <= 0 or years <= 0:
        return 0.0
    return ((end_price / start_price) ** (1 / years) - 1) * 100


def _fetch_holding_returns(symbol: str) -> dict:
    """Fetch max history for a symbol and compute annualized returns for each period."""
    if not yf:
        return {}

    from core.yf_cache import get as cache_get, put as cache_put, make_key
    cached = cache_get(make_key("holding_returns", symbol))
    if cached is not None:
        return cached

    results = {}
    try:
        ticker = yf.Ticker(_ensure_to(symbol))
        hist = ticker.history(period="max")

        if hist is None or len(hist) < 2:
            # Try without .TO
            ticker = yf.Ticker(symbol.upper())
            hist = ticker.history(period="max")

        if hist is None or len(hist) < 2:
            return results

        close = hist["Close"]
        end_price = float(close.iloc[-1])
        end_date = close.index[-1]

        # All-time return
        start_price = float(close.iloc[0])
        start_date = close.index[0]
        total_days = (end_date - start_date).days
        if total_days > 30:
            years = total_days / 365.25
            results["all"] = round(_annualized_return(start_price, end_price, years), 2)

        # Period returns
        for period_key, days in PERIODS.items():
            target_date = end_date - __import__("datetime").timedelta(days=days)
            # Find closest date at or after target
            mask = close.index >= target_date
            if mask.any():
                period_start = float(close[mask].iloc[0])
                actual_days = (end_date - close[mask].index[0]).days
                if actual_days > 30:
                    years = actual_days / 365.25
                    results[period_key.lower()] = round(_annualized_return(period_start, end_price, years), 2)

    except Exception as e:
        print(f"holdings_performance: error for {symbol}: {e}")

    cache_put(make_key("holding_returns", symbol), results)
    return results


def holdings_performance(args: dict, state: dict) -> dict:
    """Compute per-holding annualized returns."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    if not yf:
        return {"error": "yfinance package not available."}

    # Collect unique holdings with their aggregated values
    total_value = 0
    holdings_map = {}  # symbol -> {name, total_value, price}

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                sym = holding.get("symbol", "")
                val = holding.get("market_value", 0)
                if sym and val > 0:
                    total_value += val
                    if sym not in holdings_map:
                        holdings_map[sym] = {
                            "name": holding.get("name", sym),
                            "total_value": val,
                            "price": holding.get("current_price", 0),
                        }
                    else:
                        holdings_map[sym]["total_value"] += val

    if not holdings_map:
        return {"error": "No holdings with symbols found."}

    # Fetch returns for each holding
    rows = []
    for sym, info in holdings_map.items():
        returns = _fetch_holding_returns(sym)
        weight = (info["total_value"] / total_value * 100) if total_value > 0 else 0

        row = {
            "symbol": sym,
            "name": info["name"],
            "weight_pct": round(weight, 1),
            "price": round(info["price"], 2),
            "return_1y": returns.get("1y"),
            "return_3y": returns.get("3y"),
            "return_5y": returns.get("5y"),
            "return_10y": returns.get("10y"),
            "return_all": returns.get("all"),
        }
        rows.append(row)

    # Sort by weight descending
    rows.sort(key=lambda x: -x["weight_pct"])

    result = {
        "total_value": round(total_value, 2),
        "holdings_count": len(rows),
        "holdings": rows,
    }

    # --- Auto-generate dashboard widget (full-width table) ---
    table_columns = [
        {"key": "symbol", "label": "Symbol", "format": "text"},
        {"key": "name", "label": "Name", "format": "text"},
        {"key": "weight_pct", "label": "Weight %", "format": "percent"},
        {"key": "price", "label": "Price", "format": "currency"},
        {"key": "return_1y", "label": "1Y", "format": "percent"},
        {"key": "return_3y", "label": "3Y", "format": "percent"},
        {"key": "return_5y", "label": "5Y", "format": "percent"},
        {"key": "return_10y", "label": "10Y", "format": "percent"},
        {"key": "return_all", "label": "All Time", "format": "percent"},
    ]

    table_rows = []
    for r in rows:
        table_rows.append({
            "symbol": r["symbol"],
            "name": r["name"][:30],
            "weight_pct": r["weight_pct"],
            "price": r["price"],
            "return_1y": r["return_1y"] if r["return_1y"] is not None else "—",
            "return_3y": r["return_3y"] if r["return_3y"] is not None else "—",
            "return_5y": r["return_5y"] if r["return_5y"] is not None else "—",
            "return_10y": r["return_10y"] if r["return_10y"] is not None else "—",
            "return_all": r["return_all"] if r["return_all"] is not None else "—",
        })

    new_widgets = [{
        "type": "table",
        "title": "Holding Performance (Annualized Returns)",
        "data": {"columns": table_columns, "rows": table_rows},
        "gridPosition": {"col": 1, "row": 1, "colSpan": 2},
        "confidence": 0.7,
    }]

    result["new_widgets"] = new_widgets
    return result
