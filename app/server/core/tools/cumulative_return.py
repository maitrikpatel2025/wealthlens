"""Cumulative return (growth of $10,000) and annual return bar charts."""

try:
    import yfinance as yf
except ImportError:
    yf = None

CUMULATIVE_RETURN_SCHEMA = {
    "name": "cumulative_return",
    "description": "Generate growth of $10,000 chart (cumulative return line) and annual return grouped bar chart comparing portfolio vs benchmark.",
    "parameters": {
        "type": "object",
        "properties": {
            "benchmark": {
                "type": "string",
                "enum": ["XIU", "VFV", "VGRO", "VBAL", "XIC"],
                "description": "Benchmark to compare against. Default VGRO.",
            },
            "period": {
                "type": "string",
                "enum": ["1Y", "3Y", "5Y", "ALL"],
                "description": "Lookback period. Default 5Y.",
            },
        },
        "required": [],
    },
}

PERIOD_TO_YF = {
    "1Y": "1y",
    "3Y": "3y",
    "5Y": "5y",
    "ALL": "max",
}


def _ensure_to(symbol: str) -> str:
    upper = symbol.upper()
    if "." in upper:
        return upper
    return f"{upper}.TO"


def _fetch_monthly_close(symbols: list, period: str) -> dict:
    """Fetch monthly closing prices for symbols. Returns {symbol: [(date_str, price), ...]}."""
    if not yf:
        return {}

    from core.yf_cache import get as cache_get, put as cache_put, make_key

    yf_period = PERIOD_TO_YF.get(period, "5y")
    results = {}

    # Check cache first
    uncached_symbols = []
    for s in symbols:
        cached = cache_get(make_key("monthly_close", s, period))
        if cached is not None:
            results[s] = cached
        else:
            uncached_symbols.append(s)

    if not uncached_symbols:
        return results

    fetch_syms = [_ensure_to(s) for s in uncached_symbols]
    sym_map = {_ensure_to(s): s for s in uncached_symbols}

    try:
        data = yf.download(
            fetch_syms,
            period=yf_period,
            interval="1mo",
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        if data.empty:
            return results

        if len(fetch_syms) == 1:
            sym = fetch_syms[0]
            orig = sym_map[sym]
            close = data.get("Close")
            if close is not None and len(close) >= 2:
                prices = []
                for dt, price in close.items():
                    if price and price > 0:
                        date_str = dt.strftime("%Y-%m") if hasattr(dt, "strftime") else str(dt)[:7]
                        prices.append((date_str, float(price)))
                results[orig] = prices
        else:
            close = data.get("Close")
            if close is not None:
                for fs in fetch_syms:
                    orig = sym_map[fs]
                    try:
                        col = close[fs] if fs in close.columns else None
                        if col is not None:
                            clean = col.dropna()
                            if len(clean) >= 2:
                                prices = []
                                for dt, price in clean.items():
                                    if price and price > 0:
                                        date_str = dt.strftime("%Y-%m") if hasattr(dt, "strftime") else str(dt)[:7]
                                        prices.append((date_str, float(price)))
                                results[orig] = prices
                    except (KeyError, IndexError):
                        continue
    except Exception as e:
        print(f"cumulative_return: yfinance error: {e}")

    # Store fetched results in cache
    for s in uncached_symbols:
        if s in results:
            cache_put(make_key("monthly_close", s, period), results[s])

    return results


def cumulative_return(args: dict, state: dict) -> dict:
    """Compute growth of $10,000 and annual returns for portfolio vs benchmark."""
    households = state.get("households", [])
    benchmark = args.get("benchmark", "VGRO")
    period = args.get("period", "5Y")

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    if not yf:
        return {"error": "yfinance package not available."}

    # Collect symbols and weights
    total_value = 0
    symbol_values = {}

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                sym = holding.get("symbol", "")
                if sym and val > 0:
                    symbol_values[sym] = symbol_values.get(sym, 0) + val
                    total_value += val

    if total_value == 0:
        return {"error": "No holdings with market values found."}

    symbol_weights = {sym: val / total_value for sym, val in symbol_values.items()}

    # Fetch monthly closing prices
    all_symbols = list(symbol_values.keys()) + [benchmark]
    prices_data = _fetch_monthly_close(all_symbols, period)

    # Build common date index from available holdings
    available = {s: p for s, p in prices_data.items() if s in symbol_weights and len(p) >= 2}
    if not available:
        return {"error": "Could not fetch historical price data for any holdings."}

    # Find common dates across all available holdings
    date_sets = [set(d for d, _ in prices) for prices in available.values()]
    common_dates = sorted(set.intersection(*date_sets)) if date_sets else []

    if len(common_dates) < 2:
        # Fallback: use dates from the holding with the most data
        longest = max(available.values(), key=len)
        common_dates = sorted(d for d, _ in longest)

    # Build portfolio cumulative growth ($10,000)
    portfolio_growth = []
    total_weight_covered = sum(symbol_weights[s] for s in available)

    for i, date in enumerate(common_dates):
        if i == 0:
            portfolio_growth.append({"x": date, "y": 10000})
            continue

        weighted_return = 0
        for sym, weight in symbol_weights.items():
            if sym not in available:
                continue
            prices = dict(available[sym])
            prev_date = common_dates[i - 1]
            if date in prices and prev_date in prices and prices[prev_date] > 0:
                monthly_ret = (prices[date] - prices[prev_date]) / prices[prev_date]
                adj_weight = weight / total_weight_covered if total_weight_covered > 0 else weight
                weighted_return += adj_weight * monthly_ret

        prev_val = portfolio_growth[-1]["y"]
        portfolio_growth.append({"x": date, "y": round(prev_val * (1 + weighted_return), 2)})

    # Benchmark cumulative growth
    bench_growth = []
    bench_prices = prices_data.get(benchmark, [])
    if bench_prices and len(bench_prices) >= 2:
        bench_dict = dict(bench_prices)
        first_price = None
        for date in common_dates:
            if date in bench_dict:
                if first_price is None:
                    first_price = bench_dict[date]
                    bench_growth.append({"x": date, "y": 10000})
                else:
                    bench_growth.append({"x": date, "y": round(10000 * bench_dict[date] / first_price, 2)})

    # --- Annual returns grouped by year ---
    annual_returns = {}
    for i in range(1, len(common_dates)):
        year = common_dates[i][:4]
        prev_year = common_dates[i - 1][:4]
        date = common_dates[i]
        prev_date = common_dates[i - 1]

        if year not in annual_returns:
            annual_returns[year] = {"portfolio": 1.0, "benchmark": 1.0}

        # Portfolio monthly return
        port_ret = 0
        for sym, weight in symbol_weights.items():
            if sym not in available:
                continue
            prices = dict(available[sym])
            if date in prices and prev_date in prices and prices[prev_date] > 0:
                adj_weight = weight / total_weight_covered if total_weight_covered > 0 else weight
                port_ret += adj_weight * ((prices[date] - prices[prev_date]) / prices[prev_date])
        annual_returns[year]["portfolio"] *= (1 + port_ret)

        # Benchmark monthly return
        bench_dict_local = dict(bench_prices) if bench_prices else {}
        if date in bench_dict_local and prev_date in bench_dict_local and bench_dict_local[prev_date] > 0:
            b_ret = (bench_dict_local[date] - bench_dict_local[prev_date]) / bench_dict_local[prev_date]
            annual_returns[year]["benchmark"] *= (1 + b_ret)

    annual_bar_data = []
    for year in sorted(annual_returns.keys()):
        ar = annual_returns[year]
        annual_bar_data.append({
            "label": year,
            "portfolio": round((ar["portfolio"] - 1) * 100, 1),
            "benchmark": round((ar["benchmark"] - 1) * 100, 1),
        })

    result = {
        "period": period,
        "benchmark": benchmark,
        "months_analyzed": len(common_dates),
        "portfolio_final_value": portfolio_growth[-1]["y"] if portfolio_growth else 10000,
        "benchmark_final_value": bench_growth[-1]["y"] if bench_growth else None,
    }

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    # Growth of $10,000 line chart
    line_data = [{"name": "Portfolio", "data": portfolio_growth}]
    if bench_growth:
        line_data.append({"name": benchmark, "data": bench_growth})

    new_widgets.append({
        "type": "line",
        "title": f"Growth of $10,000 ({period})",
        "data": line_data,
        "confidence": 0.7,
    })

    # Annual return grouped bars
    if annual_bar_data:
        new_widgets.append({
            "type": "bar",
            "title": f"Annual Returns: Portfolio vs {benchmark}",
            "data": annual_bar_data,
            "confidence": 0.7,
        })

    result["new_widgets"] = new_widgets
    return result
