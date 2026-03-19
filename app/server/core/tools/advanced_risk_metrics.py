"""Advanced risk-adjusted performance metrics: Sharpe, Sortino, Std Dev, Max Drawdown, VaR."""

import asyncio
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import numpy as np
except ImportError:
    np = None

ADVANCED_RISK_METRICS_SCHEMA = {
    "name": "advanced_risk_metrics",
    "description": "Compute advanced risk-adjusted metrics: annualized return, std dev, Sharpe ratio, Sortino ratio, max drawdown, VaR (5%), and alpha vs benchmark. Uses monthly return series.",
    "parameters": {
        "type": "object",
        "properties": {
            "period": {
                "type": "string",
                "enum": ["1Y", "3Y", "5Y", "ALL"],
                "description": "Lookback period for computing metrics. Default 3Y.",
            },
            "benchmark": {
                "type": "string",
                "enum": ["XIU", "VFV", "VGRO", "VBAL", "XIC"],
                "description": "Benchmark to compare against. Default XIU.",
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

RISK_FREE_RATE = 0.045  # 4.5% annualized


def _ensure_to(symbol: str) -> str:
    upper = symbol.upper()
    if "." in upper:
        return upper
    return f"{upper}.TO"


def _fetch_monthly_returns(symbols: list, period: str) -> dict:
    """Fetch monthly closing prices and compute monthly returns for each symbol."""
    if not yf:
        return {}

    from core.yf_cache import get as cache_get, put as cache_put, make_key

    yf_period = PERIOD_TO_YF.get(period, "3y")
    results = {}

    # Check cache first
    uncached_symbols = []
    for s in symbols:
        cached = cache_get(make_key("monthly_returns", s, period))
        if cached is not None:
            results[s] = cached
        else:
            uncached_symbols.append(s)

    if not uncached_symbols:
        return results

    symbols_to_fetch = uncached_symbols

    fetch_syms = [_ensure_to(s) for s in symbols_to_fetch]
    sym_map = {_ensure_to(s): s for s in symbols_to_fetch}

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
            if close is not None and len(close) >= 3:
                monthly_returns = close.pct_change().dropna()
                results[orig] = monthly_returns.values.tolist()
        else:
            close = data.get("Close")
            if close is not None:
                for fs in fetch_syms:
                    orig = sym_map[fs]
                    try:
                        col = close[fs] if fs in close.columns else None
                        if col is not None:
                            clean = col.dropna()
                            if len(clean) >= 3:
                                monthly_returns = clean.pct_change().dropna()
                                results[orig] = monthly_returns.values.tolist()
                    except (KeyError, IndexError):
                        continue
    except Exception as e:
        print(f"advanced_risk: yfinance error: {e}")

    # Retry individually for missing symbols
    for s in symbols_to_fetch:
        if s not in results:
            try:
                ticker = yf.Ticker(_ensure_to(s))
                hist = ticker.history(period=yf_period, interval="1mo")
                if hist is not None and len(hist) >= 3:
                    monthly_returns = hist["Close"].pct_change().dropna()
                    results[s] = monthly_returns.values.tolist()
            except Exception:
                continue

    # Store fetched results in cache
    for s in symbols_to_fetch:
        if s in results:
            cache_put(make_key("monthly_returns", s, period), results[s])

    return results


def advanced_risk_metrics(args: dict, state: dict) -> dict:
    """Compute advanced risk metrics for the portfolio vs benchmark."""
    households = state.get("households", [])
    period = args.get("period", "3Y")
    benchmark = args.get("benchmark", "XIU")

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

    # Fetch monthly returns for all holdings + benchmark
    all_symbols = list(symbol_values.keys()) + [benchmark]
    returns_data = _fetch_monthly_returns(all_symbols, period)

    # Find common length across available holdings
    available = {s: r for s, r in returns_data.items() if s in symbol_weights}
    if not available:
        return {"error": "Could not fetch historical return data for any holdings."}

    min_len = min(len(r) for r in available.values())
    if min_len < 3:
        return {"error": "Insufficient monthly data (need at least 3 months)."}

    # Compute weighted portfolio monthly returns
    portfolio_monthly = [0.0] * min_len
    total_weight_covered = 0

    for sym, weight in symbol_weights.items():
        if sym in available:
            rets = available[sym][-min_len:]
            for i in range(min_len):
                portfolio_monthly[i] += weight * rets[i]
            total_weight_covered += weight

    # Normalize if not all holdings had data
    if total_weight_covered > 0 and total_weight_covered < 0.99:
        portfolio_monthly = [r / total_weight_covered for r in portfolio_monthly]

    # Benchmark monthly returns
    bench_monthly = returns_data.get(benchmark, [])
    if bench_monthly:
        bench_monthly = bench_monthly[-min_len:]

    # --- Compute metrics ---
    pm = portfolio_monthly

    # Annualized return: (1+r1)(1+r2)...(1+rn)^(12/n) - 1
    compound = 1.0
    for r in pm:
        compound *= (1 + r)
    years = len(pm) / 12
    ann_return = (compound ** (1 / years) - 1) * 100 if years > 0 else 0

    # Annualized std dev: monthly_std * sqrt(12)
    mean_m = sum(pm) / len(pm)
    variance = sum((r - mean_m) ** 2 for r in pm) / (len(pm) - 1) if len(pm) > 1 else 0
    monthly_std = variance ** 0.5
    ann_std = monthly_std * (12 ** 0.5) * 100

    # Sharpe: (annualized return - risk_free) / annualized std
    sharpe = (ann_return - RISK_FREE_RATE * 100) / ann_std if ann_std > 0 else None

    # Sortino: uses downside deviation only
    downside = [r for r in pm if r < 0]
    if downside:
        ds_var = sum(r ** 2 for r in downside) / len(downside)
        ds_std = (ds_var ** 0.5) * (12 ** 0.5) * 100
        sortino = (ann_return - RISK_FREE_RATE * 100) / ds_std if ds_std > 0 else None
    else:
        sortino = None

    # Max drawdown: peak-to-trough
    cumulative = [1.0]
    for r in pm:
        cumulative.append(cumulative[-1] * (1 + r))
    peak = cumulative[0]
    max_dd = 0
    for val in cumulative[1:]:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd
    max_dd *= 100

    # VaR 5%: 5th percentile of monthly returns
    sorted_returns = sorted(pm)
    idx = max(0, int(len(sorted_returns) * 0.05))
    var_5 = sorted_returns[idx] * 100

    # Benchmark metrics
    bench_ann_return = None
    bench_ann_std = None
    alpha = None
    if bench_monthly and len(bench_monthly) >= 3:
        bm = bench_monthly
        b_compound = 1.0
        for r in bm:
            b_compound *= (1 + r)
        b_years = len(bm) / 12
        bench_ann_return = (b_compound ** (1 / b_years) - 1) * 100 if b_years > 0 else 0

        b_mean = sum(bm) / len(bm)
        b_var = sum((r - b_mean) ** 2 for r in bm) / (len(bm) - 1) if len(bm) > 1 else 0
        bench_ann_std = (b_var ** 0.5) * (12 ** 0.5) * 100

        alpha = round(ann_return - bench_ann_return, 2)

    result = {
        "period": period,
        "benchmark": benchmark,
        "months_analyzed": len(pm),
        "holdings_coverage_pct": round(total_weight_covered * 100, 1),
        "portfolio_annualized_return": round(ann_return, 2),
        "benchmark_annualized_return": round(bench_ann_return, 2) if bench_ann_return is not None else None,
        "portfolio_std_dev": round(ann_std, 2),
        "benchmark_std_dev": round(bench_ann_std, 2) if bench_ann_std is not None else None,
        "sharpe_ratio": round(sharpe, 2) if sharpe is not None else None,
        "sortino_ratio": round(sortino, 2) if sortino is not None else None,
        "max_drawdown": round(max_dd, 2),
        "var_5pct": round(var_5, 2),
        "alpha": alpha,
    }

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    # Summary card with 6 key metrics
    new_widgets.append({
        "type": "summary",
        "title": f"Risk-Adjusted Metrics ({period})",
        "data": [
            {"label": "Ann. Return", "value": f"{ann_return:.1f}%"},
            {"label": "Ann. Std Dev", "value": f"{ann_std:.1f}%"},
            {"label": "Sharpe Ratio", "value": f"{sharpe:.2f}" if sharpe is not None else "N/A"},
            {"label": "Sortino Ratio", "value": f"{sortino:.2f}" if sortino is not None else "N/A"},
            {"label": "Max Drawdown", "value": f"-{max_dd:.1f}%"},
            {"label": "VaR (5%)", "value": f"{var_5:.1f}%"},
        ],
        "confidence": 0.7,
    })

    # Grouped bar: portfolio vs benchmark
    if bench_ann_return is not None and bench_ann_std is not None:
        new_widgets.append({
            "type": "bar",
            "title": f"Portfolio vs {benchmark} ({period})",
            "data": [
                {"label": "Ann. Return (%)", "portfolio": round(ann_return, 1), "benchmark": round(bench_ann_return, 1)},
                {"label": "Std Dev (%)", "portfolio": round(ann_std, 1), "benchmark": round(bench_ann_std, 1)},
                {"label": "Max Drawdown (%)", "portfolio": round(max_dd, 1), "benchmark": 0},
            ],
            "confidence": 0.7,
        })

    result["new_widgets"] = new_widgets
    return result
