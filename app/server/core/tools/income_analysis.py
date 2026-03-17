"""Portfolio income and dividend yield analysis tool."""

INCOME_ANALYSIS_SCHEMA = {
    "name": "income_analysis",
    "description": "Analyze portfolio dividend yield, estimated annual/monthly income, income type classification (Canadian dividend, foreign dividend, interest), and tax implications by account type.",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

# Income type classification based on geographic exposure and asset class
INCOME_TYPE_RULES = {
    "Canada": "Canadian Eligible Dividend",
    "United States": "Foreign Dividend (US)",
    "International Developed": "Foreign Dividend",
    "Emerging Markets": "Foreign Dividend",
    "Global": "Mixed (Canadian + Foreign)",
}


def _classify_income_type(holding: dict) -> str:
    """Classify income type based on geographic exposure and asset class."""
    asset_class = (holding.get("asset_class", "") or "").lower()

    # Fixed income / bonds
    if asset_class in ("fixed income", "bond") or "bond" in (holding.get("name", "") or "").lower():
        return "Interest Income"

    # Cash / money market
    if asset_class == "cash" or "money market" in (holding.get("name", "") or "").lower():
        return "Interest Income"

    # Determine by geographic exposure
    geo = holding.get("geographic_exposure", "")
    if geo and geo in INCOME_TYPE_RULES:
        return INCOME_TYPE_RULES[geo]

    # Fallback to country of domicile
    country = holding.get("country", "")
    if country:
        if country.lower() in ("canada", "ca"):
            return "Canadian Eligible Dividend"
        else:
            return "Foreign Dividend"

    return "Unknown"


def income_analysis(args: dict, state: dict) -> dict:
    """Analyze portfolio income: yield, estimated income, tax implications."""
    households = state.get("households", [])

    if not households:
        return {"error": "No household data available. Please upload a brokerage statement first."}

    total_value = 0
    total_annual_income = 0
    holdings_income = []
    income_by_type = {}
    income_by_account = {}

    for household in households:
        for account in household.get("accounts", []):
            acct_type = account.get("type", account.get("name", "Unknown"))

            for holding in account.get("holdings", []):
                val = holding.get("market_value", 0)
                total_value += val

                div_yield = holding.get("dividend_yield", 0) or 0
                if not isinstance(div_yield, (int, float)):
                    div_yield = 0

                annual_income = val * div_yield / 100
                total_annual_income += annual_income

                income_type = _classify_income_type(holding)

                # Track income by type
                income_by_type[income_type] = income_by_type.get(income_type, 0) + annual_income

                # Track income by account type
                income_by_account[acct_type] = income_by_account.get(acct_type, 0) + annual_income

                if div_yield > 0:
                    holdings_income.append({
                        "symbol": holding.get("symbol", "?"),
                        "name": holding.get("name", ""),
                        "market_value": round(val, 2),
                        "yield_pct": round(div_yield, 2),
                        "annual_income": round(annual_income, 2),
                        "monthly_income": round(annual_income / 12, 2),
                        "income_type": income_type,
                        "account": acct_type,
                    })

    # Sort by annual income descending
    holdings_income.sort(key=lambda x: -x["annual_income"])

    # Weighted portfolio yield
    weighted_yield = (total_annual_income / total_value * 100) if total_value > 0 else 0

    # Income by type breakdown
    income_type_breakdown = [
        {"type": k, "annual_income": round(v, 2), "percentage": round(v / total_annual_income * 100, 1) if total_annual_income > 0 else 0}
        for k, v in sorted(income_by_type.items(), key=lambda x: -x[1])
        if v > 0
    ]

    # Income by account breakdown
    income_account_breakdown = [
        {"account": k, "annual_income": round(v, 2), "percentage": round(v / total_annual_income * 100, 1) if total_annual_income > 0 else 0}
        for k, v in sorted(income_by_account.items(), key=lambda x: -x[1])
        if v > 0
    ]

    # Tax notes
    tax_notes = []

    # Check for US dividends in TFSA
    tfsa_us_income = 0
    rrsp_us_income = 0
    for h in holdings_income:
        if "US" in h["income_type"] or "Foreign" in h["income_type"]:
            if h["account"] == "TFSA":
                tfsa_us_income += h["annual_income"]
            elif h["account"] == "RRSP":
                rrsp_us_income += h["annual_income"]

    if tfsa_us_income > 0:
        withholding = round(tfsa_us_income * 0.15, 2)
        tax_notes.append({
            "note": "US withholding tax in TFSA",
            "detail": f"Estimated ${withholding:.2f}/year in unrecoverable US withholding tax (15%) on ${tfsa_us_income:.2f} of US/foreign dividends in your TFSA.",
            "impact": "negative",
        })

    if rrsp_us_income > 0:
        tax_notes.append({
            "note": "US dividends in RRSP — tax-treaty exempt",
            "detail": f"Your ${rrsp_us_income:.2f}/year in US dividends in the RRSP is exempt from US withholding tax under the Canada-US tax treaty.",
            "impact": "positive",
        })

    # Canadian dividends in non-registered
    for h in holdings_income:
        if h["income_type"] == "Canadian Eligible Dividend" and h["account"] in ("Non-Registered", "non-registered", "Taxable"):
            tax_notes.append({
                "note": "Canadian dividend tax credit available",
                "detail": "Canadian eligible dividends in non-registered accounts receive preferential tax treatment through the dividend tax credit.",
                "impact": "positive",
            })
            break

    # --- Auto-generate dashboard widgets ---
    new_widgets = []

    new_widgets.append({
        "type": "summary",
        "title": "Income Summary",
        "data": [
            {"label": "Weighted Yield", "value": f"{weighted_yield:.2f}%"},
            {"label": "Annual Income", "value": f"${total_annual_income:,.2f}"},
            {"label": "Monthly Income", "value": f"${total_annual_income / 12:,.2f}"},
            {"label": "Yield Sources", "value": str(len(holdings_income))},
        ],
        "confidence": 0.75,
    })

    if holdings_income:
        new_widgets.append({
            "type": "bar",
            "title": "Annual Income by Holding",
            "data": [{"label": h["symbol"], "value": h["annual_income"]} for h in holdings_income[:10]],
            "confidence": 0.75,
        })

    return {
        "total_value": round(total_value, 2),
        "weighted_yield_pct": round(weighted_yield, 2),
        "total_annual_income": round(total_annual_income, 2),
        "total_monthly_income": round(total_annual_income / 12, 2),
        "holdings_with_yield": len(holdings_income),
        "holdings_income": holdings_income[:20],
        "income_by_type": income_type_breakdown,
        "income_by_account": income_account_breakdown,
        "tax_notes": tax_notes,
        "new_widgets": new_widgets,
    }
