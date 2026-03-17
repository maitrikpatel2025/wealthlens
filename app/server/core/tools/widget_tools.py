"""Widget management tools for the agent."""

import uuid

ADD_WIDGET_SCHEMA = {
    "name": "add_widget",
    "description": "Add a new widget to the user's dashboard. Specify type, title, data, and optional grid position.",
    "parameters": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["pie", "bar", "line", "table", "gauge", "summary", "treemap", "sankey"],
                "description": "Widget chart type",
            },
            "title": {"type": "string", "description": "Widget title"},
            "data": {"description": "Widget data payload — structure depends on type"},
            "gridPosition": {
                "type": "object",
                "properties": {
                    "col": {"type": "integer"},
                    "row": {"type": "integer"},
                    "colSpan": {"type": "integer"},
                    "rowSpan": {"type": "integer"},
                },
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score 0-1",
            },
        },
        "required": ["type", "title", "data"],
    },
}

UPDATE_WIDGET_SCHEMA = {
    "name": "update_widget",
    "description": "Update an existing widget's data or properties by its ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "widget_id": {"type": "string"},
            "title": {"type": "string"},
            "data": {},
            "confidence": {"type": "number"},
        },
        "required": ["widget_id"],
    },
}

REMOVE_WIDGET_SCHEMA = {
    "name": "remove_widget",
    "description": "Remove a widget from the dashboard by its ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "widget_id": {"type": "string"},
        },
        "required": ["widget_id"],
    },
}


def add_widget(args: dict, state: dict) -> dict:
    """Add widget to state and return updated widgets list."""
    widgets = list(state.get("widgets", []))
    # Deduplicate: skip if a widget with the same title already exists
    title = args["title"]
    if any(w.get("title") == title for w in widgets):
        return {"widgets": widgets, "result": f"Widget '{title}' already exists — skipped duplicate."}
    widget = {
        "id": f"w-{uuid.uuid4().hex[:8]}",
        "type": args["type"],
        "title": title,
        "data": args["data"],
        "gridPosition": args.get("gridPosition"),
        "confidence": args.get("confidence"),
    }
    widgets.append(widget)
    return {"widgets": widgets, "result": f"Added widget '{title}' ({args['type']})"}


def update_widget(args: dict, state: dict) -> dict:
    """Update an existing widget."""
    widgets = list(state.get("widgets", []))
    widget_id = args["widget_id"]
    updated = []
    found = False
    for w in widgets:
        if w["id"] == widget_id:
            w = {**w}
            if "title" in args:
                w["title"] = args["title"]
            if "data" in args:
                w["data"] = args["data"]
            if "confidence" in args:
                w["confidence"] = args["confidence"]
            found = True
        updated.append(w)
    return {"widgets": updated, "result": f"Updated widget {widget_id}" if found else f"Widget {widget_id} not found"}


def remove_widget(args: dict, state: dict) -> dict:
    """Remove a widget by ID."""
    widgets = list(state.get("widgets", []))
    widget_id = args["widget_id"]
    new_widgets = [w for w in widgets if w["id"] != widget_id]
    return {"widgets": new_widgets, "result": f"Removed widget {widget_id}"}
