"""Prioritized insights ranking tool with CFA-level analysis rules."""

RANK_INSIGHTS_SCHEMA = {
    "name": "rank_insights",
    "description": "Generate and rank prioritized insights about the portfolio: fee optimization, risk assessment, concentration, home bias, yield, beta, and tax efficiency.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def rank_insights(args: dict, state: dict) -> dict:
    """Rank insights from available data with CFA-level analysis."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    insights = []
    priority = 0

    # Collect all holdings
    total_fees = 0
    total_value = 0
    high_fee_funds = []
    high_beta_holdings = []
    all_holdings = []
    account_types = set()

    for household in households:
        for account in household.get("accounts", []):
            account_types.add(account.get("type", "unknown"))
            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                mer = holding.get("mer", 0)
                total_value += val
                total_fees += val * mer / 100
                all_holdings.append(holding)

                if mer > 1.5:
                    high_fee_funds.append({
                        "name": holding.get("name", holding.get("symbol", "Unknown")),
                        "mer": mer,
                    })

                beta = holding.get("beta")
                if beta and isinstance(beta, (int, float)) and beta > 1.5:
                    high_beta_holdings.append({
                        "name": holding.get("name", holding.get("symbol", "Unknown")),
                        "beta": beta,
                    })

    # --- 1. HIGH-FEE FUNDS ---
    if high_fee_funds:
        priority += 1
        fee_names = [f["name"] for f in high_fee_funds[:5]]
        total_high_fee_drag = sum(
            h.get("market_value", 0) * h.get("mer", 0) / 100
            for h in all_holdings if h.get("mer", 0) > 1.5
        )
        insights.append({
            "priority": priority,
            "category": "fees",
            "title": "High-fee funds detected",
            "description": f"{len(high_fee_funds)} holding(s) have MERs above 1.5%, costing approximately ${total_high_fee_drag:,.2f}/year in fees. Consider lower-cost ETF alternatives. Use compute_fees with show_alternatives=true for specific suggestions.",
            "impact": "high",
            "funds": fee_names,
        })

    # --- 2. QUANTIFIED FEE DRAG ---
    if total_value > 0:
        weighted_mer = total_fees / total_value * 100
        if weighted_mer > 0.50:
            # 10-year fee drag with 6% assumed return
            ten_year_drag = total_value * ((1.06) ** 10) - total_value * ((1.06 - weighted_mer / 100) ** 10)
            priority += 1
            insights.append({
                "priority": priority,
                "category": "fees",
                "title": "Significant fee drag",
                "description": f"Portfolio weighted MER of {weighted_mer:.2f}% results in ${total_fees:,.2f}/year in fees. Over 10 years, this could cost approximately ${ten_year_drag:,.0f} in compounding fee drag (assuming 6% annual return).",
                "impact": "high" if weighted_mer > 1.0 else "medium",
            })

    # --- 3. HIGH BETA HOLDINGS ---
    if high_beta_holdings:
        priority += 1
        beta_names = [f"{h['name']} (β={h['beta']})" for h in high_beta_holdings[:5]]
        insights.append({
            "priority": priority,
            "category": "risk",
            "title": "High-volatility holdings",
            "description": f"{len(high_beta_holdings)} holding(s) have beta above 1.5, indicating significantly higher volatility than the market: {', '.join(beta_names)}.",
            "impact": "medium",
            "funds": [h["name"] for h in high_beta_holdings[:5]],
        })

    # --- 4. CONCENTRATION RISK ---
    symbol_totals: dict = {}
    for household in households:
        for account in household.get("accounts", []):
            for holding in account.get("holdings", []):
                sym = holding.get("symbol", "Unknown")
                symbol_totals[sym] = symbol_totals.get(sym, 0) + holding.get("market_value", 0)

    if total_value > 0:
        concentrated = [(s, v / total_value * 100) for s, v in symbol_totals.items() if v / total_value > 0.15]
        if concentrated:
            priority += 1
            conc_details = [f"{s} ({pct:.1f}%)" for s, pct in concentrated]
            insights.append({
                "priority": priority,
                "category": "concentration",
                "title": "Concentration risk",
                "description": f"{len(concentrated)} holding(s) represent more than 15% of your portfolio: {', '.join(conc_details)}. Consider diversifying to reduce single-holding risk.",
                "impact": "medium",
                "symbols": [s for s, _ in concentrated],
            })

    # --- 5. CANADIAN HOME BIAS ---
    geo_totals = {}
    for h in all_holdings:
        geo = h.get("geographic_exposure", h.get("country", "Unknown"))
        if not geo or geo == "None":
            geo = "Unknown"
        geo_totals[geo] = geo_totals.get(geo, 0) + h.get("market_value", 0)

    if total_value > 0:
        canada_val = sum(v for k, v in geo_totals.items() if k.lower() in ("canada", "ca"))
        canada_pct = canada_val / total_value * 100
        if canada_pct > 70:
            priority += 1
            insights.append({
                "priority": priority,
                "category": "diversification",
                "title": "Significant Canadian home bias",
                "description": f"{canada_pct:.1f}% of your portfolio is allocated to Canada. Canada represents only ~3% of global equity markets. Consider adding international exposure through ETFs like XAW, XEQT, or VXC for better diversification.",
                "impact": "medium",
            })

    # --- 6. LOW YIELD ---
    total_income = 0
    holdings_with_yield = 0
    for h in all_holdings:
        dy = h.get("dividend_yield", 0) or 0
        if isinstance(dy, (int, float)) and dy > 0:
            total_income += h.get("market_value", 0) * dy / 100
            holdings_with_yield += 1

    if total_value > 0 and holdings_with_yield > 0:
        portfolio_yield = total_income / total_value * 100
        if portfolio_yield < 1.0:
            priority += 1
            insights.append({
                "priority": priority,
                "category": "income",
                "title": "Low portfolio yield",
                "description": f"Portfolio weighted yield of {portfolio_yield:.2f}% generates approximately ${total_income:,.2f}/year. If income is a goal, consider higher-yielding ETFs like VDY, XEI, or ZDV.",
                "impact": "low",
            })

    # --- 7. TAX EFFICIENCY ---
    if "TFSA" not in account_types and total_value > 0:
        priority += 1
        insights.append({
            "priority": priority,
            "category": "tax_efficiency",
            "title": "No TFSA detected",
            "description": "Consider utilizing a Tax-Free Savings Account for tax-efficient growth. Investment gains and income in a TFSA are completely tax-free.",
            "impact": "medium",
        })

    # Check for US dividends in TFSA (withholding tax drag)
    for household in households:
        for account in household.get("accounts", []):
            if account.get("type") == "TFSA":
                for h in account.get("holdings", []):
                    geo = h.get("geographic_exposure", "")
                    dy = h.get("dividend_yield", 0) or 0
                    if geo in ("United States", "US") and dy > 0:
                        withholding = h.get("market_value", 0) * dy / 100 * 0.15
                        if withholding > 50:  # Only flag if material
                            priority += 1
                            insights.append({
                                "priority": priority,
                                "category": "tax_efficiency",
                                "title": "US withholding tax in TFSA",
                                "description": f"US-exposed holdings in your TFSA are subject to 15% withholding tax on dividends. Consider holding US-dividend-paying investments in your RRSP instead (exempt under Canada-US tax treaty).",
                                "impact": "medium",
                            })
                            break
                break

    if not insights:
        insights.append({
            "priority": 1,
            "category": "general",
            "title": "Portfolio looks balanced",
            "description": "No major issues detected. Consider regular rebalancing and contribution planning.",
            "impact": "low",
        })

    # --- Auto-generate dashboard widget ---
    new_widgets = []
    if insights:
        new_widgets.append({
            "type": "table",
            "title": "Portfolio Insights",
            "data": {
                "columns": ["Priority", "Category", "Insight", "Impact"],
                "rows": [
                    [str(i["priority"]), i["category"].replace("_", " ").title(), i["title"], i["impact"].title()]
                    for i in insights[:10]
                ],
            },
            "confidence": 0.8,
        })

    return {"insights": insights, "total_value": round(total_value, 2), "new_widgets": new_widgets}
