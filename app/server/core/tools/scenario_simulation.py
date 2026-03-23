"""Scenario simulation engine: stress-test portfolio against market scenarios."""

SCENARIO_SIMULATION_SCHEMA = {
    "name": "scenario_simulation",
    "description": (
        "Simulate the impact of market scenarios (bear market, rate hike, recession, "
        "sector rotation, bull run) on the portfolio. Shows projected impact on each "
        "holding based on beta, sector, asset class, and geographic exposure."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "scenario": {
                "type": "string",
                "enum": ["bear_market", "rate_hike", "sector_rotation", "recession", "bull_run"],
                "description": "The market scenario to simulate.",
            },
            "severity": {
                "type": "string",
                "enum": ["mild", "moderate", "severe"],
                "description": "Severity of the scenario. Defaults to moderate.",
            },
        },
        "required": ["scenario"],
    },
}

SEVERITY_MULTIPLIERS = {
    "mild": 0.5,
    "moderate": 1.0,
    "severe": 1.5,
}

SCENARIO_PERSONAS = {
    "bear_market": {
        "label": "Bear Market",
        "market_return": -0.25,
        "sector_impacts": {
            "Technology": -0.30,
            "Consumer Discretionary": -0.25,
            "Financials": -0.20,
            "Industrials": -0.18,
            "Energy": -0.15,
            "Materials": -0.15,
            "Communication Services": -0.20,
            "Health Care": -0.08,
            "Consumer Staples": -0.05,
            "Utilities": -0.03,
            "Real Estate": -0.18,
        },
        "asset_class_impacts": {
            "Equity": -0.22,
            "Fixed Income": 0.04,
            "Cash": 0.0,
            "Alternative": -0.10,
            "Real Estate": -0.15,
        },
        "geo_impacts": {
            "US": -0.25,
            "Canada": -0.20,
            "International": -0.22,
            "Emerging Markets": -0.30,
            "Global": -0.24,
        },
    },
    "rate_hike": {
        "label": "Rate Hike",
        "market_return": -0.08,
        "sector_impacts": {
            "Technology": -0.15,
            "Consumer Discretionary": -0.10,
            "Financials": 0.05,
            "Industrials": -0.05,
            "Energy": 0.02,
            "Materials": -0.03,
            "Communication Services": -0.10,
            "Health Care": -0.04,
            "Consumer Staples": -0.02,
            "Utilities": -0.12,
            "Real Estate": -0.18,
        },
        "asset_class_impacts": {
            "Equity": -0.06,
            "Fixed Income": -0.08,
            "Cash": 0.02,
            "Alternative": -0.03,
            "Real Estate": -0.15,
        },
        "geo_impacts": {
            "US": -0.08,
            "Canada": -0.06,
            "International": -0.07,
            "Emerging Markets": -0.12,
            "Global": -0.08,
        },
    },
    "sector_rotation": {
        "label": "Sector Rotation",
        "market_return": 0.0,
        "sector_impacts": {
            "Technology": -0.15,
            "Consumer Discretionary": -0.10,
            "Financials": 0.10,
            "Industrials": 0.08,
            "Energy": 0.12,
            "Materials": 0.08,
            "Communication Services": -0.08,
            "Health Care": 0.05,
            "Consumer Staples": 0.06,
            "Utilities": 0.04,
            "Real Estate": 0.02,
        },
        "asset_class_impacts": {
            "Equity": 0.0,
            "Fixed Income": 0.01,
            "Cash": 0.0,
            "Alternative": 0.02,
            "Real Estate": 0.03,
        },
        "geo_impacts": {
            "US": -0.02,
            "Canada": 0.04,
            "International": 0.03,
            "Emerging Markets": 0.02,
            "Global": 0.0,
        },
    },
    "recession": {
        "label": "Recession",
        "market_return": -0.30,
        "sector_impacts": {
            "Technology": -0.25,
            "Consumer Discretionary": -0.35,
            "Financials": -0.28,
            "Industrials": -0.25,
            "Energy": -0.20,
            "Materials": -0.22,
            "Communication Services": -0.18,
            "Health Care": -0.08,
            "Consumer Staples": -0.05,
            "Utilities": -0.06,
            "Real Estate": -0.25,
        },
        "asset_class_impacts": {
            "Equity": -0.28,
            "Fixed Income": 0.06,
            "Cash": 0.0,
            "Alternative": -0.12,
            "Real Estate": -0.20,
        },
        "geo_impacts": {
            "US": -0.28,
            "Canada": -0.25,
            "International": -0.26,
            "Emerging Markets": -0.35,
            "Global": -0.28,
        },
    },
    "bull_run": {
        "label": "Bull Run",
        "market_return": 0.25,
        "sector_impacts": {
            "Technology": 0.35,
            "Consumer Discretionary": 0.28,
            "Financials": 0.20,
            "Industrials": 0.22,
            "Energy": 0.15,
            "Materials": 0.18,
            "Communication Services": 0.25,
            "Health Care": 0.12,
            "Consumer Staples": 0.08,
            "Utilities": 0.05,
            "Real Estate": 0.15,
        },
        "asset_class_impacts": {
            "Equity": 0.25,
            "Fixed Income": -0.02,
            "Cash": 0.0,
            "Alternative": 0.10,
            "Real Estate": 0.12,
        },
        "geo_impacts": {
            "US": 0.26,
            "Canada": 0.20,
            "International": 0.18,
            "Emerging Markets": 0.22,
            "Global": 0.23,
        },
    },
}


def _resolve_geo(holding: dict) -> str:
    """Resolve geographic exposure for a holding."""
    geo = (holding.get("geographic_exposure") or holding.get("country") or "").strip()
    geo_lower = geo.lower()
    if "canada" in geo_lower or geo_lower == "ca":
        return "Canada"
    if "us" in geo_lower or "united states" in geo_lower or "america" in geo_lower:
        return "US"
    if "emerging" in geo_lower or "em" == geo_lower:
        return "Emerging Markets"
    if "global" in geo_lower or "world" in geo_lower:
        return "Global"
    if geo:
        return "International"
    return "Global"


def _compute_holding_impact(holding: dict, persona: dict, severity_mult: float) -> float:
    """Compute projected impact percentage for a single holding."""
    market_return = persona["market_return"]
    sector = holding.get("sector", "Unknown") or "Unknown"
    asset_class = holding.get("asset_class", "Unknown") or "Unknown"
    beta = holding.get("beta")
    if not isinstance(beta, (int, float)):
        beta = 1.0
    geo = _resolve_geo(holding)

    asset_class_impact = persona["asset_class_impacts"].get(asset_class, market_return)
    sector_impact = persona["sector_impacts"].get(sector, 0)
    geo_impact = persona["geo_impacts"].get(geo, 0)

    raw_impact = asset_class_impact + (beta - 1) * 0.5 * market_return + sector_impact + geo_impact
    return raw_impact * severity_mult


def scenario_simulation(args: dict, state: dict) -> dict:
    """Run scenario simulation on portfolio."""
    households = state.get("households", [])
    scenario_key = args.get("scenario", "bear_market")
    severity = args.get("severity", "moderate")

    if not households:
        return {"error": "No portfolio data available. Please upload a brokerage statement first."}

    if scenario_key not in SCENARIO_PERSONAS:
        return {"error": f"Unknown scenario: {scenario_key}. Choose from: {', '.join(SCENARIO_PERSONAS.keys())}"}

    persona = SCENARIO_PERSONAS[scenario_key]
    severity_mult = SEVERITY_MULTIPLIERS.get(severity, 1.0)

    # Compute per-holding impacts
    holdings_data = []
    sector_before = {}
    sector_after = {}
    total_before = 0
    total_after = 0

    for h in households:
        for acct in h.get("accounts", []):
            for holding in acct.get("holdings", []):
                val = holding.get("market_value", 0)
                if val <= 0:
                    continue

                impact_pct = _compute_holding_impact(holding, persona, severity_mult)
                impact_dollar = val * impact_pct
                new_val = val + impact_dollar
                sector = holding.get("sector", "Other") or "Other"
                symbol = holding.get("symbol", holding.get("name", "Unknown"))

                holdings_data.append({
                    "symbol": symbol,
                    "name": holding.get("name", symbol),
                    "sector": sector,
                    "current_value": round(val, 2),
                    "impact_pct": round(impact_pct * 100, 2),
                    "impact_dollar": round(impact_dollar, 2),
                    "projected_value": round(new_val, 2),
                })

                sector_before[sector] = sector_before.get(sector, 0) + val
                sector_after[sector] = sector_after.get(sector, 0) + new_val
                total_before += val
                total_after += new_val

    # Sort holdings by impact (worst first)
    holdings_data.sort(key=lambda x: x["impact_pct"])

    total_impact_pct = ((total_after - total_before) / total_before * 100) if total_before > 0 else 0
    total_impact_dollar = total_after - total_before

    # Build widgets
    new_widgets = []

    # Summary widget
    new_widgets.append({
        "type": "summary",
        "title": f"Scenario: {persona['label']} ({severity.title()})",
        "data": [
            {"label": "Current Value", "value": f"${total_before:,.0f}", "format": "text"},
            {"label": "Projected Value", "value": f"${total_after:,.0f}", "format": "text"},
            {"label": "Impact", "value": f"{total_impact_pct:+.1f}%", "format": "text"},
            {"label": "Dollar Impact", "value": f"${total_impact_dollar:+,.0f}", "format": "text"},
        ],
        "confidence": 0.6,
    })

    # Bar chart: sector impact before/after
    sector_bar_data = []
    for sector in sorted(sector_before.keys()):
        sector_bar_data.append({
            "label": sector,
            "before": round(sector_before.get(sector, 0), 0),
            "after": round(sector_after.get(sector, 0), 0),
        })

    new_widgets.append({
        "type": "bar",
        "title": f"Sector Impact: {persona['label']}",
        "data": sector_bar_data,
        "gridPosition": {"col": 1, "row": 2, "colSpan": 2},
        "confidence": 0.6,
    })

    # Table: per-holding impact
    new_widgets.append({
        "type": "table",
        "title": "Holdings Impact Detail",
        "data": {
            "columns": [
                {"key": "symbol", "label": "Symbol", "format": "text"},
                {"key": "sector", "label": "Sector", "format": "text"},
                {"key": "current_value", "label": "Current", "format": "currency"},
                {"key": "impact_pct", "label": "Impact %", "format": "percent"},
                {"key": "impact_dollar", "label": "Impact $", "format": "currency"},
                {"key": "projected_value", "label": "Projected", "format": "currency"},
            ],
            "rows": holdings_data,
        },
        "confidence": 0.6,
    })

    return {
        "scenario": scenario_key,
        "severity": severity,
        "total_before": round(total_before, 2),
        "total_after": round(total_after, 2),
        "total_impact_pct": round(total_impact_pct, 2),
        "total_impact_ili": round(total_impact_dollar, 2),
        "holdings_count": len(holdings_data),
        "new_widgets": new_widgets,
    }
