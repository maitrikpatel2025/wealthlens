"""Simple in-memory cache for yfinance data to avoid redundant API calls."""

import time
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
_TTL = 300  # 5 minutes


def get(key: str) -> Any | None:
    """Get cached value if not expired."""
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < _TTL:
            return val
        del _cache[key]
    return None


def put(key: str, value: Any) -> None:
    """Store value in cache."""
    _cache[key] = (time.time(), value)


def make_key(prefix: str, *args) -> str:
    """Build a cache key from prefix and args."""
    return f"{prefix}:{'|'.join(str(a) for a in args)}"
