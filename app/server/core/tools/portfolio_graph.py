"""Portfolio knowledge graph: builds node-link graph of portfolio relationships."""

PORTFOLIO_GRAPH_SCHEMA = {
    "name": "portfolio_graph",
    "description": (
        "Build a knowledge graph of portfolio relationships showing connections between "
        "holdings, sectors, asset classes, accounts, and geographies. Returns nodes and "
        "links for force-directed or radial visualization."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "focus": {
                "type": "string",
                "enum": ["full", "sectors", "geography", "accounts", "asset_classes"],
                "description": "Which dimensions to include. Defaults to full.",
            },
        },
        "required": [],
    },
}

NODE_COLORS = {
    "holding": "#22c55e",
    "sector": "#f59e0b",
    "asset_class": "#a855f7",
    "account": "#3b82f6",
    "geography": "#06b6d4",
}


def portfolio_graph(args: dict, state: dict) -> dict:
    """Build a knowledge graph of portfolio relationships."""
    households = state.get("households", [])
    focus = args.get("focus", "full")

    if not households:
        return {"error": "No portfolio data available. Please upload a brokerage statement first."}

    nodes = {}
    links = []
    total_value = 0

    # First pass: compute total for weight calculations
    for h in households:
        for acct in h.get("accounts", []):
            for holding in acct.get("holdings", []):
                total_value += holding.get("market_value", 0)

    if total_value <= 0:
        return {"error": "Portfolio has no market value data."}

    # Second pass: build nodes and links
    for h in households:
        for acct in h.get("accounts", []):
            acct_name = acct.get("account_type", acct.get("name", "Unknown Account"))
            acct_id = f"acct:{acct_name}"

            if focus in ("full", "accounts") and acct_id not in nodes:
                acct_value = sum(hld.get("market_value", 0) for hld in acct.get("holdings", []))
                nodes[acct_id] = {
                    "id": acct_id,
                    "label": acct_name,
                    "type": "account",
                    "value": round(acct_value, 2),
                    "weight_pct": round(acct_value / total_value * 100, 2) if total_value > 0 else 0,
                    "color": NODE_COLORS["account"],
                }

            for holding in acct.get("holdings", []):
                val = holding.get("market_value", 0)
                if val <= 0:
                    continue

                symbol = holding.get("symbol", holding.get("name", "Unknown"))
                holding_id = f"holding:{symbol}"
                weight_pct = round(val / total_value * 100, 2)

                # Holding node
                if holding_id not in nodes:
                    nodes[holding_id] = {
                        "id": holding_id,
                        "label": symbol,
                        "type": "holding",
                        "value": round(val, 2),
                        "weight_pct": weight_pct,
                        "color": NODE_COLORS["holding"],
                    }
                else:
                    nodes[holding_id]["value"] = round(nodes[holding_id]["value"] + val, 2)
                    nodes[holding_id]["weight_pct"] = round(nodes[holding_id]["value"] / total_value * 100, 2)

                # Account link
                if focus in ("full", "accounts"):
                    links.append({
                        "source": holding_id,
                        "target": acct_id,
                        "type": "held_in",
                        "value": round(val, 2),
                    })

                # Sector
                sector = holding.get("sector", "Unknown") or "Unknown"
                if focus in ("full", "sectors") and sector != "Unknown":
                    sector_id = f"sector:{sector}"
                    if sector_id not in nodes:
                        nodes[sector_id] = {
                            "id": sector_id,
                            "label": sector,
                            "type": "sector",
                            "value": 0,
                            "weight_pct": 0,
                            "color": NODE_COLORS["sector"],
                        }
                    nodes[sector_id]["value"] = round(nodes[sector_id]["value"] + val, 2)
                    nodes[sector_id]["weight_pct"] = round(nodes[sector_id]["value"] / total_value * 100, 2)
                    links.append({
                        "source": holding_id,
                        "target": sector_id,
                        "type": "belongs_to",
                        "value": round(val, 2),
                    })

                # Asset class
                asset_class = holding.get("asset_class", "Unknown") or "Unknown"
                if focus in ("full", "asset_classes") and asset_class != "Unknown":
                    ac_id = f"asset_class:{asset_class}"
                    if ac_id not in nodes:
                        nodes[ac_id] = {
                            "id": ac_id,
                            "label": asset_class,
                            "type": "asset_class",
                            "value": 0,
                            "weight_pct": 0,
                            "color": NODE_COLORS["asset_class"],
                        }
                    nodes[ac_id]["value"] = round(nodes[ac_id]["value"] + val, 2)
                    nodes[ac_id]["weight_pct"] = round(nodes[ac_id]["value"] / total_value * 100, 2)
                    links.append({
                        "source": holding_id,
                        "target": ac_id,
                        "type": "classified_as",
                        "value": round(val, 2),
                    })

                # Geography
                geo = (holding.get("geographic_exposure") or holding.get("country") or "").strip()
                if focus in ("full", "geography") and geo:
                    geo_id = f"geography:{geo}"
                    if geo_id not in nodes:
                        nodes[geo_id] = {
                            "id": geo_id,
                            "label": geo,
                            "type": "geography",
                            "value": 0,
                            "weight_pct": 0,
                            "color": NODE_COLORS["geography"],
                        }
                    nodes[geo_id]["value"] = round(nodes[geo_id]["value"] + val, 2)
                    nodes[geo_id]["weight_pct"] = round(nodes[geo_id]["value"] / total_value * 100, 2)
                    links.append({
                        "source": holding_id,
                        "target": geo_id,
                        "type": "exposed_to",
                        "value": round(val, 2),
                    })

    node_list = list(nodes.values())
    new_widgets = [
        {
            "type": "graph",
            "title": "Portfolio Knowledge Graph",
            "data": {
                "nodes": node_list,
                "links": links,
                "total_value": round(total_value, 2),
                "node_count": len(node_list),
                "link_count": len(links),
            },
            "gridPosition": {"col": 1, "row": 1, "colSpan": 2},
            "confidence": 0.7,
        },
    ]

    return {
        "focus": focus,
        "total_value": round(total_value, 2),
        "node_count": len(node_list),
        "link_count": len(links),
        "new_widgets": new_widgets,
    }
