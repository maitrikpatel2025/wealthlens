"""
Enrichment sub-agent — FMP stable API + yfinance fallback.
Resolves symbols, fetches live market data (price, sector, asset_class, MER).
Also fetches CFA-level fields: beta, dividend_yield, country, geographic_exposure,
market_cap, market_cap_class, pe_ratio, fifty_two_week_high/low.
Uses FMP /stable/profile (works for .TO Canadian ETFs) with yfinance fallback for mutual funds.
"""

import os
import asyncio
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import httpx
except ImportError:
    httpx = None

# Canadian ETF suffix
CA_SUFFIX = ".TO"

# Known Canadian mutual fund prefixes (not on FMP)
MUTUAL_FUND_PREFIXES = ("TDB", "RBF", "MAW", "DYN", "FID", "CIG", "AIM", "MFC", "SUN", "GWL", "IGI", "NBI")

# Geographic exposure mapping for well-known ETFs
# Key: symbol (without .TO suffix, uppercase) → actual investment region
ETF_GEOGRAPHIC_EXPOSURE = {
    # S&P 500 / US equity
    "VFV": "United States", "VOO": "United States", "SPY": "United States",
    "IVV": "United States", "VUN": "United States", "XUS": "United States",
    "ZSP": "United States", "HXS": "United States", "QQC": "United States",
    "QQQ": "United States", "XQQ": "United States", "ZNQ": "United States",
    "VGG": "United States", "ZUE": "United States",
    # Canadian equity
    "XIC": "Canada", "XIU": "Canada", "ZCN": "Canada", "VCN": "Canada",
    "HXT": "Canada", "XEI": "Canada", "CDZ": "Canada", "VDY": "Canada",
    "ZDV": "Canada", "PDC": "Canada",
    # Global / All-world equity
    "XEQT": "Global", "VEQT": "Global", "VXC": "Global", "XAW": "Global",
    "ZGQ": "Global", "HGRO": "Global",
    # Balanced (global)
    "VGRO": "Global", "VBAL": "Global", "XGRO": "Global", "XBAL": "Global",
    "ZBAL": "Global", "ZGRO": "Global", "VCNS": "Global", "VCIP": "Global",
    # Canadian bonds
    "ZAG": "Canada", "XBB": "Canada", "VAB": "Canada", "ZFL": "Canada",
    "XLB": "Canada", "ZDB": "Canada", "CLF": "Canada",
    # International developed
    "XEF": "International Developed", "VIU": "International Developed",
    "ZEA": "International Developed", "VI": "International Developed",
    # Emerging markets
    "VEE": "Emerging Markets", "XEM": "Emerging Markets", "ZEM": "Emerging Markets",
    # US-listed broad
    "VTI": "United States", "SCHB": "United States", "IWM": "United States",
    "VT": "Global", "VXUS": "International Developed",
}

# Keywords in fund names to infer geographic exposure
GEO_NAME_KEYWORDS = [
    ("s&p 500", "United States"), ("s&p500", "United States"),
    ("u.s.", "United States"), ("us equity", "United States"),
    ("us total", "United States"), ("american", "United States"),
    ("nasdaq", "United States"), ("dow jones", "United States"),
    ("tsx", "Canada"), ("canadian", "Canada"), ("canada", "Canada"),
    ("s&p/tsx", "Canada"),
    ("international", "International Developed"), ("developed", "International Developed"),
    ("eafe", "International Developed"), ("europe", "International Developed"),
    ("emerging", "Emerging Markets"),
    ("global", "Global"), ("all-world", "Global"), ("world", "Global"),
    ("all equity", "Global"), ("all cap", "Global"),
    ("aggregate bond", "Canada"), ("canadian bond", "Canada"),
    ("universe bond", "Canada"),
]


async def enrichment_agent(holdings: list, state: dict) -> list:
    """
    Enrich holdings with live market data.
    For each holding: resolve symbol → fetch price, sector, asset class, MER,
    plus CFA-level fields: beta, yield, country, geographic exposure, market cap, P/E, 52-week range.
    """
    enriched = []
    cache = state.get("enrichment_cache", {})

    tasks = [_enrich_single(h, cache) for h in holdings]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for h, result in zip(holdings, results):
        if isinstance(result, Exception):
            print(f"Enrichment error for {h.get('symbol', '?')}: {result}")
            enriched.append({**h})
        else:
            enriched.append(result)

    return enriched


async def _enrich_single(holding: dict, cache: dict) -> dict:
    """Enrich a single holding with market data."""
    enriched = {**holding}
    symbol = holding.get("symbol", "")
    name = holding.get("name", "")

    # Resolve symbol if missing
    if not symbol and name:
        symbol = await resolve_symbol(name)
        if symbol:
            enriched["symbol"] = symbol

    if not symbol:
        return enriched

    # Check cache first
    if symbol in cache:
        enriched.update(cache[symbol])
        return enriched

    # Determine if this is a mutual fund code (not on FMP)
    is_mutual_fund = any(symbol.upper().startswith(p) for p in MUTUAL_FUND_PREFIXES)

    if is_mutual_fund:
        market_data = await _fetch_yfinance(symbol)
    else:
        # Try FMP first, fallback to yfinance for price
        market_data = await _fetch_fmp_profile(symbol)
        if not market_data.get("current_price"):
            market_data = await _fetch_yfinance(symbol)
        else:
            # FMP returned price — still call yfinance for fields FMP doesn't provide
            # (beta, dividend_yield, pe_ratio, 52-week range, market_cap)
            yf_data = await _fetch_yfinance(symbol)
            # Merge: yfinance fills gaps, FMP takes priority for shared fields
            for key in ("beta", "dividend_yield", "pe_ratio",
                        "fifty_two_week_high", "fifty_two_week_low",
                        "market_cap", "mer"):
                if key in yf_data and yf_data[key]:
                    market_data.setdefault(key, yf_data[key])
            # Also fill country if FMP didn't have it
            if not market_data.get("country") and yf_data.get("country"):
                market_data["country"] = yf_data["country"]

    # Infer geographic exposure for ETFs
    asset_class = market_data.get("asset_class", enriched.get("asset_class", ""))
    if asset_class in ("ETF", "Mutual Fund") or not asset_class:
        geo = _infer_geographic_exposure(
            market_data.get("company_name", name),
            symbol
        )
        if geo:
            market_data["geographic_exposure"] = geo

    # Compute market cap classification
    mc = market_data.get("market_cap")
    if mc and isinstance(mc, (int, float)) and mc > 0:
        if mc >= 10_000_000_000:
            market_data["market_cap_class"] = "Large Cap"
        elif mc >= 2_000_000_000:
            market_data["market_cap_class"] = "Mid Cap"
        else:
            market_data["market_cap_class"] = "Small Cap"

    # Classify style (Value / Blend / Growth) — check ETF overrides first
    clean_sym = symbol.upper().replace(".TO", "")
    if clean_sym in ETF_STYLE_OVERRIDES:
        override_cap, override_style = ETF_STYLE_OVERRIDES[clean_sym]
        market_data["market_cap_class"] = market_data.get("market_cap_class") or override_cap
        market_data["style_class"] = override_style
    else:
        style = _classify_style(
            market_data.get("pe_ratio") or enriched.get("pe_ratio"),
            market_data.get("price_to_book") or enriched.get("price_to_book"),
        )
        if style:
            market_data["style_class"] = style

    enriched.update(market_data)
    return enriched


async def resolve_symbol(name: str, isin: str = "") -> str:
    """Resolve a fund name to a ticker symbol using FMP search or heuristics."""
    fmp_key = os.getenv("FMP_API_KEY", "")

    # Try FMP search-name endpoint
    if fmp_key and httpx:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://financialmodelingprep.com/stable/search-name",
                    params={"query": name[:50], "apikey": fmp_key},
                )
                if resp.status_code == 200:
                    results = resp.json()
                    if results:
                        # Prefer TSX-listed
                        for r in results:
                            sym = r.get("symbol", "")
                            if sym.endswith(CA_SUFFIX) or "TSX" in r.get("exchangeShortName", ""):
                                return sym
                        return results[0].get("symbol", "")
        except Exception:
            pass

    # Fallback: yfinance direct lookup
    if yf and name:
        try:
            clean = name.split(" ")[0].upper()
            for suffix in [f"{clean}.TO", clean]:
                try:
                    info = yf.Ticker(suffix).info
                    if info and info.get("regularMarketPrice"):
                        return suffix
                except Exception:
                    pass
        except Exception:
            pass

    return ""


async def _fetch_fmp_profile(symbol: str) -> dict:
    """Fetch market data from FMP /stable/profile endpoint."""
    fmp_key = os.getenv("FMP_API_KEY", "")
    if not fmp_key or not httpx:
        return {}

    # Ensure Canadian symbols have .TO suffix
    query_symbol = _ensure_ca_suffix(symbol)

    data: dict = {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://financialmodelingprep.com/stable/profile",
                params={"symbol": query_symbol, "apikey": fmp_key},
            )
            if resp.status_code == 200:
                results = resp.json()
                if results and isinstance(results, list) and len(results) > 0:
                    p = results[0]
                    data["current_price"] = p.get("price", 0)
                    data["currency"] = p.get("currency", "CAD")
                    data["exchange"] = p.get("exchangeFullName", "")
                    data["sector"] = p.get("sector", "Unknown")
                    data["industry"] = p.get("industry", "")
                    data["company_name"] = p.get("companyName", "")

                    # CFA-level fields from FMP profile
                    if p.get("beta"):
                        data["beta"] = round(float(p["beta"]), 2)
                    if p.get("lastDiv") and p.get("price") and p["price"] > 0:
                        data["dividend_yield"] = round(float(p["lastDiv"]) / float(p["price"]) * 100, 2)
                    if p.get("mktCap"):
                        data["market_cap"] = p["mktCap"]
                    if p.get("country"):
                        data["country"] = p["country"]

                    # Determine asset class
                    if p.get("isEtf"):
                        data["asset_class"] = "ETF"
                    elif p.get("isFund"):
                        data["asset_class"] = "Mutual Fund"
                    elif p.get("isAdr"):
                        data["asset_class"] = "ADR"
                    else:
                        data["asset_class"] = _infer_asset_class_from_name(
                            p.get("companyName", ""), symbol
                        )

            # If profile returned empty, try without .TO
            if not data and query_symbol != symbol:
                resp2 = await client.get(
                    "https://financialmodelingprep.com/stable/profile",
                    params={"symbol": symbol, "apikey": fmp_key},
                )
                if resp2.status_code == 200:
                    results2 = resp2.json()
                    if results2 and isinstance(results2, list) and len(results2) > 0:
                        p = results2[0]
                        data["current_price"] = p.get("price", 0)
                        data["currency"] = p.get("currency", "USD")
                        data["exchange"] = p.get("exchangeFullName", "")
                        data["sector"] = p.get("sector", "Unknown")
                        data["industry"] = p.get("industry", "")
                        data["asset_class"] = "ETF" if p.get("isEtf") else "Equity"

                        # CFA-level fields
                        if p.get("beta"):
                            data["beta"] = round(float(p["beta"]), 2)
                        if p.get("lastDiv") and p.get("price") and p["price"] > 0:
                            data["dividend_yield"] = round(float(p["lastDiv"]) / float(p["price"]) * 100, 2)
                        if p.get("mktCap"):
                            data["market_cap"] = p["mktCap"]
                        if p.get("country"):
                            data["country"] = p["country"]

    except Exception as e:
        print(f"FMP profile error for {query_symbol}: {e}")

    return data


async def _fetch_yfinance(symbol: str) -> dict:
    """Fetch market data from yfinance (fallback)."""
    if not yf:
        return {}

    data: dict = {}
    query_symbol = _ensure_ca_suffix(symbol)

    try:
        # Run yfinance in thread pool (it's synchronous)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _yf_get_info, query_symbol)

        if not info or not info.get("regularMarketPrice"):
            # Try without .TO suffix
            if query_symbol != symbol:
                info = await loop.run_in_executor(None, _yf_get_info, symbol)

        if info and info.get("regularMarketPrice"):
            data["current_price"] = info.get("regularMarketPrice", info.get("previousClose", 0))
            data["currency"] = info.get("currency", "CAD")
            data["sector"] = info.get("sector", "Unknown")
            data["industry"] = info.get("industry", "")
            data["exchange"] = info.get("exchange", "")
            data["company_name"] = info.get("longName", info.get("shortName", ""))

            # Asset class from quote type
            qt = info.get("quoteType", "").lower()
            if qt == "etf":
                data["asset_class"] = "ETF"
            elif qt == "mutualfund":
                data["asset_class"] = "Mutual Fund"
            elif qt == "equity":
                data["asset_class"] = "Equity"
            else:
                data["asset_class"] = _infer_asset_class_from_name(
                    info.get("longName", ""), symbol
                )

            # MER / expense ratio — store in percent format (e.g. 0.09 means 0.09%)
            expense = info.get("annualReportExpenseRatio") or info.get("totalExpenseRatio")
            if expense and expense > 0:
                data["mer"] = round(expense * 100, 3)

            # --- CFA-level fields from yfinance ---
            # Beta
            beta = info.get("beta") or info.get("beta3Year")
            if beta and isinstance(beta, (int, float)):
                data["beta"] = round(float(beta), 2)

            # Dividend yield (yfinance returns as decimal, e.g. 0.025 = 2.5%)
            div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
            if div_yield and isinstance(div_yield, (int, float)) and div_yield > 0:
                data["dividend_yield"] = round(float(div_yield) * 100, 2)

            # Country
            country = info.get("country")
            if country:
                data["country"] = country

            # Market cap
            market_cap = info.get("marketCap") or info.get("totalAssets")
            if market_cap and isinstance(market_cap, (int, float)):
                data["market_cap"] = market_cap

            # P/E ratio
            pe = info.get("trailingPE") or info.get("forwardPE")
            if pe and isinstance(pe, (int, float)) and pe > 0:
                data["pe_ratio"] = round(float(pe), 2)

            # 52-week high/low
            high_52 = info.get("fiftyTwoWeekHigh")
            low_52 = info.get("fiftyTwoWeekLow")
            if high_52 and isinstance(high_52, (int, float)):
                data["fifty_two_week_high"] = round(float(high_52), 2)
            if low_52 and isinstance(low_52, (int, float)):
                data["fifty_two_week_low"] = round(float(low_52), 2)

            # --- Fundamental fields (Phase 1) ---
            ptb = info.get("priceToBook")
            if ptb and isinstance(ptb, (int, float)) and ptb > 0:
                data["price_to_book"] = round(float(ptb), 2)

            pts = info.get("priceToSalesTrailing12Months")
            if pts and isinstance(pts, (int, float)) and pts > 0:
                data["price_to_sales"] = round(float(pts), 2)

            roe_val = info.get("returnOnEquity")
            if roe_val and isinstance(roe_val, (int, float)):
                data["roe"] = round(float(roe_val) * 100, 2)

            roa_val = info.get("returnOnAssets")
            if roa_val and isinstance(roa_val, (int, float)):
                data["roa"] = round(float(roa_val) * 100, 2)

            dte = info.get("debtToEquity")
            if dte and isinstance(dte, (int, float)):
                data["debt_to_equity"] = round(float(dte), 2)

            fpe = info.get("forwardPE")
            if fpe and isinstance(fpe, (int, float)) and fpe > 0:
                data["forward_pe"] = round(float(fpe), 2)

            # Gross expense ratio (separate from net MER)
            ger = info.get("grossExpenseRatio") or info.get("annualReportExpenseRatio")
            if ger and isinstance(ger, (int, float)) and ger > 0:
                data["gross_expense_ratio"] = round(float(ger) * 100, 3)

            # Fund load fees
            fl = info.get("maxFrontEndSalesLoad") or info.get("frontEndSalesLoad")
            if fl and isinstance(fl, (int, float)) and fl > 0:
                data["front_load"] = round(float(fl) * 100, 2)

            dl = info.get("maxDeferredSalesLoad") or info.get("deferredSalesLoad")
            if dl and isinstance(dl, (int, float)) and dl > 0:
                data["deferred_load"] = round(float(dl) * 100, 2)

            # SEC yields
            sy7 = info.get("sevenDayYield")
            if sy7 and isinstance(sy7, (int, float)):
                data["sec_yield_7day"] = round(float(sy7) * 100, 2)

            sy30 = info.get("thirtyDayYield")
            if sy30 and isinstance(sy30, (int, float)):
                data["sec_yield_30day"] = round(float(sy30) * 100, 2)

    except Exception as e:
        print(f"yfinance error for {query_symbol}: {e}")

    return data


def _yf_get_info(symbol: str) -> dict:
    """Synchronous yfinance info fetch."""
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


def _ensure_ca_suffix(symbol: str) -> str:
    """Add .TO suffix for known Canadian ETF/stock symbols without it."""
    if not symbol:
        return symbol
    upper = symbol.upper()
    # Already has exchange suffix
    if "." in upper:
        return upper
    # Mutual fund codes — don't add .TO
    if any(upper.startswith(p) for p in MUTUAL_FUND_PREFIXES):
        return upper
    # Common Canadian ETF symbols — add .TO
    return f"{upper}.TO"


def _infer_asset_class_from_name(name: str, symbol: str) -> str:
    """Infer asset class from fund/company name."""
    name_lower = name.lower()
    if "bond" in name_lower or "fixed income" in name_lower or "aggregate" in name_lower:
        return "Fixed Income"
    if "money market" in name_lower or "cash" in name_lower:
        return "Cash"
    if "balanced" in name_lower:
        return "Balanced"
    if "dividend" in name_lower:
        return "Equity"
    if "index" in name_lower or "etf" in name_lower:
        return "ETF"
    return "Unknown"


def _classify_style(pe: float | None, pb: float | None) -> str:
    """Classify investment style using P/E + P/B thresholds.
    Value: low P/E (<15) or low P/B (<1.5)
    Growth: high P/E (>25) or high P/B (>4)
    Blend: everything else
    """
    if pe is None and pb is None:
        return ""
    score = 0  # negative = value, positive = growth
    if pe is not None:
        if pe < 15:
            score -= 1
        elif pe > 25:
            score += 1
    if pb is not None:
        if pb < 1.5:
            score -= 1
        elif pb > 4:
            score += 1
    if score < 0:
        return "Value"
    elif score > 0:
        return "Growth"
    return "Blend"


# Well-known ETF style overrides for multi-asset/balanced ETFs
# that don't have meaningful P/E/P/B at the fund level
ETF_STYLE_OVERRIDES = {
    "VGRO": ("Mid Cap", "Blend"),
    "VBAL": ("Mid Cap", "Blend"),
    "XGRO": ("Mid Cap", "Blend"),
    "XBAL": ("Mid Cap", "Blend"),
    "ZGRO": ("Mid Cap", "Blend"),
    "ZBAL": ("Mid Cap", "Blend"),
    "VCNS": ("Mid Cap", "Blend"),
    "VCIP": ("Mid Cap", "Blend"),
    "VEQT": ("Large Cap", "Blend"),
    "XEQT": ("Large Cap", "Blend"),
    "VFV": ("Large Cap", "Growth"),
    "VOO": ("Large Cap", "Growth"),
    "SPY": ("Large Cap", "Growth"),
    "XIU": ("Large Cap", "Blend"),
    "XIC": ("Large Cap", "Blend"),
    "VCN": ("Large Cap", "Blend"),
    "ZCN": ("Large Cap", "Blend"),
    "VUN": ("Large Cap", "Growth"),
    "XUS": ("Large Cap", "Growth"),
    "QQC": ("Large Cap", "Growth"),
    "XEF": ("Large Cap", "Blend"),
    "VIU": ("Large Cap", "Blend"),
    "VEE": ("Mid Cap", "Blend"),
    "XEM": ("Mid Cap", "Blend"),
}


def _infer_geographic_exposure(name: str, symbol: str) -> str:
    """
    Infer the actual geographic investment exposure for ETFs/funds.
    This is distinct from country of domicile — e.g., VFV is domiciled in Canada
    but has 100% US equity exposure.
    """
    # Strip .TO suffix for lookup
    clean_symbol = symbol.upper().replace(".TO", "").replace(".V", "")

    # Direct lookup first
    if clean_symbol in ETF_GEOGRAPHIC_EXPOSURE:
        return ETF_GEOGRAPHIC_EXPOSURE[clean_symbol]

    # Keyword matching on fund name
    if name:
        name_lower = name.lower()
        for keyword, region in GEO_NAME_KEYWORDS:
            if keyword in name_lower:
                return region

    return ""
