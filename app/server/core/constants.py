"""
Shared constants for WealthLens.

Centralizes hardcoded values used across the backend.
"""

# Upload limits
MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

# Currency
DEFAULT_CURRENCY = "CAD"

# Widget types (must match frontend WidgetType in widgets.ts)
WIDGET_TYPES = [
    "pie",
    "bar",
    "line",
    "table",
    "gauge",
    "summary",
    "treemap",
    "sankey",
]

# Account types recognized by the system
ACCOUNT_TYPES = [
    "RRSP",
    "TFSA",
    "Non-Registered",
    "RESP",
    "LIRA",
    "Corporate",
]

# Supported file types for upload
SUPPORTED_FILE_TYPES = [
    ".pdf",
]
