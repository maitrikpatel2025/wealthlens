"""What-If Simulation Engine: re-run analytics on hypothetical portfolio changes."""

import copy

SIMULATE_REBALANCE_SCHEMA = {
    "name": "simulate_rebalance",
    "description": (
        "Simulate hypothetical portfolio changes (sell, buy, adjust_weight) and show "
        "before vs after comparison of key metrics: total value, weighted MER, annual fees, "
        "yield, asset class mix. Original portfolio data is never modified."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "changes": {
                "type": "array",
                "description": "List of hypothetical changes to apply.",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["sell", "buy", "adjust_weight"],
                            "description": "sell = remove amount from symbol, buy = add new position, adjust_weight = set target % weight.",
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol to act on.",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Dollar amount for sell/buy, or target percentage for adjust_weight.",
                        },
                        "target_symbol": {
                            "type": "string",
                            "description": "For sell: optionally reinvest proceeds into this symbol.",
                        },
                    },
                    "required": ["action", "symbol"],
                },
            },
        },
        "required": ["changes"],
    },
}


def _compute_metrics(households: list) -> dict:
    """Compute portfolio-level metrics from households."""
    total_value = 0
    total_fees = 0
    total_income = 0
    asset_classes: dict[str, float] = {}
    beta_sum = 0
    beta_weight = 0

    for h in households:
        for acct in h.get("accounts", []):
            for holding in acct.get("holdings", []):
                val = holding.get("market_value", 0)
                mer = holding.get("mer", 0)
                dy = holding.get("dividend_yield", 0) or 0
                b = holding.get("beta")
                ac = holding.get("asset_class", "Unknown") or "Unknown"

                total_value += val
                total_fees += val * mer / 100
                total_income += val * dy / 100
                asset_classes[ac] = asset_classes.get(ac, 0) + val

                if b and isinstance(b, (int, float)):
                    beta_sum += b * val
                    beta_weight += val

    weighted_mer = (total_fees / total_value * 100) if total_value > 0 else 0
    weighted_yield = (total_income / total_value * 100) if total_value > 0 else 0
    weighted_beta = (beta_sum / beta_weight) if beta_weight > 0 else None

    ac_pct = {k: round(v / total_value * 100, 1) if total_value > 0 else 0 for k, v in asset_classes.items()}

    return {
        "total_value": round(total_value, 2),
        "weighted_mer": round(weighted_mer, 3),
        "annual_fees": round(total_fees, 2),
        "weighted_yield": round(weighted_yield, 2),
        "annual_income": round(total_income, 2),
        "weighted_beta": round(weighted_beta, 2) if weighted_beta else None,
        "asset_class_mix": ac_pct,
    }


def _find_holding(households: list, symbol: str):
    """Find a holding by symbol across all households. Returns (holding, account) or (None, None)."""
    symbol_upper = symbol.upper()
    for h in households:
        for acct in h.get("accounts", []):
            for holding in acct.get("holdings", []):
                if (holding.get("symbol", "").upper() == symbol_upper):
                    return holding, acct
    return None, None


def _apply_changes(households: list, changes: list) -> list:
    """Deep-copy households and apply hypothetical changes."""
    sim = copy.deepcopy(households)

    for change in changes:
        action = change.get("action", "")
        symbol = change.get("symbol", "")
        amount = change.get("amount", 0)
        target_symbol = change.get("target_symbol")

        if action == "sell":
            holding, acct = _find_holding(sim, symbol)
            if holding:
                sell_val = min(amount or holding["market_value"], holding["market_value"])
                holding["market_value"] = round(holding["market_value"] - sell_val, 2)
                if holding.get("current_price") and holding["current_price"] > 0:
                    holding["quantity"] = round(holding["market_value"] / holding["current_price"], 4)

                # Reinvest into target if specified
                if target_symbol and sell_val > 0:
                    target, t_acct = _find_holding(sim, target_symbol)
                    if target:
                        target["market_value"] = round(target["market_value"] + sell_val, 2)
                        if target.get("current_price") and target["current_price"] > 0:
                            target["quantity"] = round(target["market_value"] / target["current_price"], 4)
                    elif acct:
                        # Create new position in same account
                        acct["holdings"].append({
                            "symbol": target_symbol,
                            "name": target_symbol,
                            "market_value": round(sell_val, 2),
                            "quantity": 0,
                            "mer": 0.20,  # assume low-cost ETF
                            "asset_class": "Equity",
                        })

        elif action == "buy":
            holding, acct = _find_holding(sim, symbol)
            if holding:
                holding["market_value"] = round(holding["market_value"] + (amount or 0), 2)
                if holding.get("current_price") and holding["current_price"] > 0:
                    holding["quantity"] = round(holding["market_value"] / holding["current_price"], 4)
            else:
                # Add new holding to first account
                if sim and sim[0].get("accounts"):
                    sim[0]["accounts"][0].setdefault("holdings", []).append({
                        "symbol": symbol,
                        "name": symbol,
                        "market_value": round(amount or 0, 2),
                        "quantity": 0,
                        "mer": 0.20,
                        "asset_class": "Equity",
                    })

        elif action == "adjust_weight":
            # Compute current total and rebalance
            total = sum(
                h2.get("market_value", 0)
                for hh in sim for a in hh.get("accounts", []) for h2 in a.get("holdings", [])
            )
            holding, _ = _find_holding(sim, symbol)
            if holding and total > 0:
                target_val = total * (amount or 0) / 100
                holding["market_value"] = round(target_val, 2)
                if holding.get("current_price") and holding["current_price"] > 0:
                    holding["quantity"] = round(target_val / holding["current_price"], 4)

    # Remove zero-value holdings
    for h in sim:
        for acct in h.get("accounts", []):
            acct["holdings"] = [hld for hld in acct.get("holdings", []) if hld.get("market_value", 0) > 0]

    return sim


def simulate_rebalance(args: dict, state: dict) -> dict:
    """Run what-if simulation and return before/after comparison."""
    households = state.get("households", [])
    changes = args.get("changes", [])

    if not households:
        return {"error": "No portfolio data available. Please upload a brokerage statement first."}
    if not changes:
        return {"error": "No changes specified. Provide at least one sell/buy/adjust_weight change."}

    before = _compute_metrics(households)
    simulated = _apply_changes(households, changes)
    after = _compute_metrics(simulated)

    # Compute deltas
    deltas = {}
    for key in ["total_value", "weighted_mer", "annual_fees", "weighted_yield", "annual_income"]:
        b = before.get(key, 0) or 0
        a = after.get(key, 0) or 0
        deltas[key] = round(a - b, 3)

    # Generate widgets
    comparison_items = [
        {"label": "Total Value", "before": before["total_value"], "after": after["total_value"]},
        {"label": "Weighted MER %", "before": before["weighted_mer"], "after": after["weighted_mer"]},
        {"label": "Annual Fees", "before": before["annual_fees"], "after": after["annual_fees"]},
        {"label": "Yield %", "before": before["weighted_yield"], "after": after["weighted_yield"]},
        {"label": "Annual Income", "before": before["annual_income"], "after": after["annual_income"]},
    ]

    new_widgets = [
        {
            "type": "bar",
            "title": "Simulation: Before vs After",
            "data": comparison_items,
            "gridPosition": {"col": 1, "row": 1, "colSpan": 2},
            "confidence": 0.7,
        },
    ]

    # Asset class mix comparison table
    all_classes = sorted(set(list(before["asset_class_mix"].keys()) + list(after["asset_class_mix"].keys())))
    if all_classes:
        mix_rows = []
        for ac in all_classes:
            b_pct = before["asset_class_mix"].get(ac, 0)
            a_pct = after["asset_class_mix"].get(ac, 0)
            mix_rows.append({"asset_class": ac, "before_pct": b_pct, "after_pct": a_pct, "change": round(a_pct - b_pct, 1)})
        new_widgets.append({
            "type": "table",
            "title": "Asset Mix: Before vs After",
            "data": {
                "columns": [
                    {"key": "asset_class", "label": "Asset Class", "format": "text"},
                    {"key": "before_pct", "label": "Before %", "format": "percent"},
                    {"key": "after_pct", "label": "After %", "format": "percent"},
                    {"key": "change", "label": "Change", "format": "percent"},
                ],
                "rows": mix_rows,
            },
            "confidence": 0.7,
        })

    return {
        "before": before,
        "after": after,
        "deltas": deltas,
        "changes_applied": changes,
        "new_widgets": new_widgets,
    }
