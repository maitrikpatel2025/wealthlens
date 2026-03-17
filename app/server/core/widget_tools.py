"""
Widget tool schemas and execution for WealthLens agent.
Tools: add_widget, update_widget, remove_widget
"""

import uuid
from typing import Any


def make_widget_id() -> str:
    return f"w-{uuid.uuid4().hex[:8]}"


# --- Tool schemas for LLM function calling ---

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
                "description": "Optional grid placement",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score 0-1 for the data accuracy",
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
            "widget_id": {"type": "string", "description": "ID of widget to update"},
            "title": {"type": "string"},
            "data": {"description": "New data payload"},
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
            "widget_id": {"type": "string", "description": "ID of widget to remove"},
        },
        "required": ["widget_id"],
    },
}

ALL_WIDGET_SCHEMAS = [ADD_WIDGET_SCHEMA, UPDATE_WIDGET_SCHEMA, REMOVE_WIDGET_SCHEMA]


# --- Tool execution ---

def execute_add_widget(args: dict, widgets: list) -> list:
    """Add a widget and return updated widget list."""
    widget = {
        "id": make_widget_id(),
        "type": args["type"],
        "title": args["title"],
        "data": args["data"],
        "gridPosition": args.get("gridPosition"),
        "confidence": args.get("confidence"),
    }
    return widgets + [widget]


def execute_update_widget(args: dict, widgets: list) -> list:
    """Update a widget by ID and return updated list."""
    updated = []
    for w in widgets:
        if w["id"] == args["widget_id"]:
            w = {**w}
            if "title" in args:
                w["title"] = args["title"]
            if "data" in args:
                w["data"] = args["data"]
            if "confidence" in args:
                w["confidence"] = args["confidence"]
        updated.append(w)
    return updated


def execute_remove_widget(args: dict, widgets: list) -> list:
    """Remove a widget by ID and return updated list."""
    return [w for w in widgets if w["id"] != args["widget_id"]]
