"""Portfolio vs benchmark performance comparison using yfinance historical data."""

import asyncio
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    yf = None

COMPARE_PERFORMANCE_SCHEMA = {
    "name": "compare_performance",
    "description": "Compare portfolio performance against a Canadian benchmark using historical price data. Computes weighted portfolio return and alpha vs benchmark.",
    "parameters": {
        "type": "object",
        "properties": {
            "benchmark": {
                "type": "string",
                "enum": ["XIU", "VFV", "VGRO", "VBAL", "XIC"],
                "description": "Benchmark to compare against. XIU = S&P/TSX Composite, VFV = S&P 500 CAD, VGRO = Growth balanced, VBAL = Conservative balanced, XIC = S&P/TSX Capped.",
            },
            "period": {
                "type": "string",
                "enum": ["1M", "3M", "6M", "1Y", "3Y", "5Y", "YTD"],
                "description": "Time period for comparison. Default 1Y.",
            },
        },
        "required": [],
    },
}

# Map period strings to yfinance period format and approximate days
PERIOD_MAP = {
    "1M": {"yf_period": "1mo", "days": 30},
    "3M": {"yf_period": "3mo", "days": 90},
    "6M": {"yf_period": "6mo", "days": 180},
    "1Y": {"yf_period": "1y", "days": 365},
    "3Y": {"yf_period": "3y", "days": 1095},
    "5Y": {"yf_period": "5y", "days": 1825},
    "YTD": {"yf_period": "ytd", "days": None},
}


def _ensure_to_suffix(symbol: str) -> str:
    """Add .TO suffix for Canadian symbols if not already present."""
    upper = symbol.upper()
    if "." in upper:
        return upper
    return f"{upper}.TO"


def _fetch_returns(symbols: list, period_key: str) -> dict:
    """
    Fetch historical price returns for a list of symbols using yfinance.
    Returns dict: {symbol: return_pct} where return_pct is a float (e.g., 12.5 = 12.5%).
    """
    if not yf:
        return {}

    period_info = PERIOD_MAP.get(period_key, PERIOD_MAP["1Y"])
    yf_period = period_info["yf_period"]

    returns = {}

    # Build list of symbols to fetch (add .TO for Canadian)
    fetch_symbols = []
    symbol_map = {}  # fetch_symbol -> original_symbol
    for sym in symbols:
        fetch_sym = _ensure_to_suffix(sym) if "." not in sym.upper() else sym.upper()
        fetch_symbols.append(fetch_sym)
        symbol_map[fetch_sym] = sym

    if not fetch_symbols:
        return returns

    try:
        # Batch download for efficiency
        data = yf.download(
            fetch_symbols,
            period=yf_period,
            auto_adjust=True,
            progress=False,
            threads=True,
        )

        if data.empty:
            return returns

        # Handle single vs multi-symbol DataFrame structure
        if len(fetch_symbols) == 1:
            sym = fetch_symbols[0]
            orig = symbol_map[sym]
            close = data.get("Close")
            if close is not None and len(close) >= 2:
                start_price = close.iloc[0]
                end_price = close.iloc[-1]
                if start_price and start_price > 0:
                    returns[orig] = round((end_price - start_price) / start_price * 100, 2)
        else:
            close = data.get("Close")
            if close is not None:
                for fetch_sym in fetch_symbols:
                    orig = symbol_map[fetch_sym]
                    try:
                        col = close[fetch_sym] if fetch_sym in close.columns else None
                        if col is not None and len(col.dropna()) >= 2:
                            clean = col.dropna()
                            start_price = clean.iloc[0]
                            end_price = clean.iloc[-1]
                            if start_price and start_price > 0:
                                returns[orig] = round((end_price - start_price) / start_price * 100, 2)
                    except (KeyError, IndexError):
                        continue

    except Exception as e:
        print(f"yfinance download error: {e}")

    # Retry individually for any that failed (without .TO suffix)
    for sym in symbols:
        if sym not in returns:
            try:
                ticker = yf.Ticker(sym.upper())
                hist = ticker.history(period=yf_period)
                if hist is not None and len(hist) >= 2:
                    close = hist["Close"]
                    start_price = close.iloc[0]
                    end_price = close.iloc[-1]
                    if start_price and start_price > 0:
                        returns[sym] = round((end_price - start_price) / start_price * 100, 2)
            except Exception:
                continue

    return returns


def compare_performance(args: dict, state: dict) -> dict:
    """Compare portfolio to benchmark using historical price data from yfinance."""
    households = state.get("households", [])
    benchmark = args.get("benchmark", "XIU")
    period = args.get("period", "1Y")

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    if not yf:
        return {"error": "yfinance package not available. Cannot fetch historical performance data."}

    # Collect all unique symbols and their weights
    total_value = 0
    symbol_values = {}  # symbol -> total market value

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

    # Compute weights
    symbol_weights = {sym: val / total_value for sym, val in symbol_values.items()}

    # Fetch returns for all holdings + benchmark
    all_symbols = list(symbol_values.keys()) + [benchmark]
    returns = _fetch_returns(all_symbols, period)

    # Compute weighted portfolio return
    portfolio_return = 0.0
    holdings_with_returns = []
    missing_symbols = []

    for sym, weight in symbol_weights.items():
        ret = returns.get(sym)
        if ret is not None:
            contribution = weight * ret
            portfolio_return += contribution
            holdings_with_returns.append({
                "symbol": sym,
                "weight": round(weight * 100, 2),
                "return_pct": ret,
                "contribution": round(contribution, 2),
                "value": round(symbol_values[sym], 2),
            })
        else:
            missing_symbols.append(sym)

    portfolio_return = round(portfolio_return, 2)

    # Benchmark return
    benchmark_return = returns.get(benchmark)

    # Alpha
    alpha = None
    if benchmark_return is not None:
        alpha = round(portfolio_return - benchmark_return, 2)

    # Sort holdings by contribution (descending)
    holdings_with_returns.sort(key=lambda x: -abs(x["contribution"]))

    result = {
        "portfolio_total": round(total_value, 2),
        "portfolio_return_pct": portfolio_return,
        "benchmark": benchmark,
        "benchmark_return_pct": benchmark_return,
        "alpha": alpha,
        "period": period,
        "holdings_returns": holdings_with_returns[:20],
        "holdings_count": len(symbol_weights),
        "holdings_with_data": len(holdings_with_returns),
    }

    if missing_symbols:
        result["missing_data"] = missing_symbols[:10]
        result["note"] = f"Could not fetch historical data for {len(missing_symbols)} holding(s). Portfolio return is based on {len(holdings_with_returns)} of {len(symbol_weights)} holdings."

    if benchmark_return is None:
        result["note"] = (result.get("note", "") + f" Could not fetch benchmark ({benchmark}) return data.").strip()

    # --- Auto-generate dashboard widget ---
    new_widgets = []
    bar_data = [{"label": "Portfolio", "value": portfolio_return}]
    if benchmark_return is not None:
        bar_data.append({"label": benchmark, "value": benchmark_return})
    new_widgets.append({
        "type": "bar",
        "title": f"Performance: Portfolio vs {benchmark} ({period})",
        "data": bar_data,
        "confidence": 0.7,
    })
    result["new_widgets"] = new_widgets

    return result
