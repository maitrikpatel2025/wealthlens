"""Portfolio risk analysis tool — beta, concentration, geographic exposure, market cap distribution."""

PORTFOLIO_RISK_SCHEMA = {
    "name": "portfolio_risk",
    "description": "Comprehensive portfolio risk analysis: weighted beta, risk classification, sector/geographic/market cap concentration, top-5 holding concentration, and risk flags.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def portfolio_risk(args: dict, state: dict) -> dict:
    """Compute comprehensive portfolio risk metrics."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    # Collect all holdings with values
    all_holdings = []
    total_value = 0

    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                if val > 0:
                    all_holdings.append(holding)
                    total_value += val

    if total_value == 0:
        return {"error": "No holdings with market values found."}

    # --- Weighted Portfolio Beta ---
    weighted_beta = 0.0
    beta_coverage = 0.0  # What % of portfolio has beta data
    holdings_with_beta = 0

    for h in all_holdings:
        weight = h.get("market_value", 0) / total_value
        beta = h.get("beta")
        if beta and isinstance(beta, (int, float)):
            weighted_beta += weight * beta
            beta_coverage += weight
            holdings_with_beta += 1

    weighted_beta = round(weighted_beta, 2) if beta_coverage > 0 else None

    # Risk classification
    risk_label = "Unknown"
    if weighted_beta is not None:
        if weighted_beta < 0.8:
            risk_label = "Defensive"
        elif weighted_beta <= 1.2:
            risk_label = "Moderate"
        else:
            risk_label = "Aggressive"

    # --- Top-5 Concentration ---
    symbol_values = {}
    for h in all_holdings:
        sym = h.get("symbol", h.get("name", "Unknown"))
        symbol_values[sym] = symbol_values.get(sym, 0) + h.get("market_value", 0)

    sorted_holdings = sorted(symbol_values.items(), key=lambda x: -x[1])
    top_5 = sorted_holdings[:5]
    top_5_value = sum(v for _, v in top_5)
    top_5_pct = round(top_5_value / total_value * 100, 2) if total_value > 0 else 0

    top_5_details = [
        {"symbol": sym, "value": round(val, 2), "percentage": round(val / total_value * 100, 2)}
        for sym, val in top_5
    ]

    # --- Sector Concentration ---
    sector_totals = {}
    for h in all_holdings:
        sector = h.get("sector", "Unknown")
        if not sector or sector == "None":
            sector = "Unknown"
        sector_totals[sector] = sector_totals.get(sector, 0) + h.get("market_value", 0)

    sector_breakdown = [
        {"name": k, "value": round(v, 2), "percentage": round(v / total_value * 100, 2)}
        for k, v in sorted(sector_totals.items(), key=lambda x: -x[1])
    ]

    # --- Geographic Exposure ---
    geo_totals = {}
    for h in all_holdings:
        geo = h.get("geographic_exposure", h.get("country", "Unknown"))
        if not geo or geo == "None":
            geo = "Unknown"
        geo_totals[geo] = geo_totals.get(geo, 0) + h.get("market_value", 0)

    geo_breakdown = [
        {"name": k, "value": round(v, 2), "percentage": round(v / total_value * 100, 2)}
        for k, v in sorted(geo_totals.items(), key=lambda x: -x[1])
    ]

    # Home bias detection
    canada_pct = 0
    for g in geo_breakdown:
        if g["name"].lower() in ("canada", "ca"):
            canada_pct += g["percentage"]
    home_bias = canada_pct > 60

    # --- Market Cap Distribution ---
    cap_totals = {}
    for h in all_holdings:
        cap = h.get("market_cap_class", "Unknown")
        if not cap or cap == "None":
            cap = "Unknown"
        cap_totals[cap] = cap_totals.get(cap, 0) + h.get("market_value", 0)

    cap_breakdown = [
        {"name": k, "value": round(v, 2), "percentage": round(v / total_value * 100, 2)}
        for k, v in sorted(cap_totals.items(), key=lambda x: -x[1])
    ]

    # --- Risk Flags ---
    risk_flags = []

    if weighted_beta is not None and weighted_beta > 1.5:
        risk_flags.append({
            "flag": "High Portfolio Beta",
            "detail": f"Portfolio beta of {weighted_beta} indicates significantly higher volatility than the market.",
            "severity": "high",
        })

    if top_5_pct > 70:
        risk_flags.append({
            "flag": "Extreme Concentration",
            "detail": f"Top 5 holdings represent {top_5_pct}% of portfolio. Consider diversifying.",
            "severity": "high",
        })
    elif top_5_pct > 50:
        risk_flags.append({
            "flag": "Moderate Concentration",
            "detail": f"Top 5 holdings represent {top_5_pct}% of portfolio.",
            "severity": "medium",
        })

    if home_bias:
        risk_flags.append({
            "flag": "Canadian Home Bias",
            "detail": f"{canada_pct:.1f}% of portfolio is invested in Canada. Consider international diversification.",
            "severity": "medium",
        })

    # Single holding > 25%
    for sym, val in sorted_holdings:
        pct = val / total_value * 100
        if pct > 25:
            risk_flags.append({
                "flag": "Single-Holding Dominance",
                "detail": f"{sym} represents {pct:.1f}% of portfolio.",
                "severity": "high",
            })

    # Sector concentration > 40%
    for s in sector_breakdown:
        if s["percentage"] > 40 and s["name"] != "Unknown":
            risk_flags.append({
                "flag": "Sector Concentration",
                "detail": f"{s['name']} sector represents {s['percentage']}% of portfolio.",
                "severity": "medium",
            })

    if not risk_flags:
        risk_flags.append({
            "flag": "No Major Risk Flags",
            "detail": "Portfolio risk profile appears balanced.",
            "severity": "low",
        })

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    if weighted_beta is not None:
        new_widgets.append({
            "type": "gauge",
            "title": "Portfolio Risk Score",
            "data": {
                "value": weighted_beta,
                "min": 0,
                "max": 2,
                "label": risk_label,
                "thresholds": [
                    {"value": 0.8, "color": "#22c55e"},
                    {"value": 1.2, "color": "#f59e0b"},
                    {"value": 2.0, "color": "#ef4444"},
                ],
            },
            "confidence": 0.75,
        })

    if geo_breakdown:
        geo_data = [{"name": g["name"], "value": g["percentage"]} for g in geo_breakdown if g["name"] != "Unknown"]
        if geo_data:
            new_widgets.append({
                "type": "pie",
                "title": "Geographic Exposure",
                "data": geo_data,
                "confidence": 0.75,
            })

    return {
        "total_value": round(total_value, 2),
        "holdings_count": len(all_holdings),
        "weighted_beta": weighted_beta,
        "beta_coverage_pct": round(beta_coverage * 100, 1),
        "risk_classification": risk_label,
        "top_5_concentration": {
            "percentage": top_5_pct,
            "holdings": top_5_details,
        },
        "sector_breakdown": sector_breakdown[:10],
        "geographic_breakdown": geo_breakdown[:10],
        "home_bias_detected": home_bias,
        "canada_allocation_pct": round(canada_pct, 1),
        "market_cap_breakdown": cap_breakdown,
        "risk_flags": risk_flags,
        "new_widgets": new_widgets,
    }
