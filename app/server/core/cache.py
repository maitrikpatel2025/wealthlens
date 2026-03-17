"""
Redis caching for WealthLens.
- Market data cache: 1hr TTL
- Symbol resolution cache: 24hr TTL
"""

import os
import json
from typing import Optional

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

_redis_client = None

MARKET_DATA_TTL = 3600       # 1 hour
SYMBOL_RESOLUTION_TTL = 86400  # 24 hours


async def get_redis():
    """Get or create Redis client."""
    global _redis_client

    if not HAS_REDIS:
        return None

    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            _redis_client = aioredis.from_url(redis_url, decode_responses=True)
            await _redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            _redis_client = None

    return _redis_client


async def cache_get(key: str) -> Optional[dict]:
    """Get a cached value."""
    client = await get_redis()
    if not client:
        return None

    try:
        value = await client.get(f"wl:{key}")
        if value:
            return json.loads(value)
    except Exception:
        pass

    return None


async def cache_set(key: str, value: dict, ttl: int = MARKET_DATA_TTL):
    """Set a cached value with TTL."""
    client = await get_redis()
    if not client:
        return

    try:
        await client.set(f"wl:{key}", json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def cache_market_data(symbol: str, data: dict):
    """Cache market data for a symbol (1hr TTL)."""
    await cache_set(f"market:{symbol}", data, MARKET_DATA_TTL)


async def get_cached_market_data(symbol: str) -> Optional[dict]:
    """Get cached market data for a symbol."""
    return await cache_get(f"market:{symbol}")


async def cache_symbol_resolution(name: str, symbol: str):
    """Cache a symbol resolution (24hr TTL)."""
    await cache_set(f"symbol:{name}", {"symbol": symbol}, SYMBOL_RESOLUTION_TTL)


async def get_cached_symbol(name: str) -> Optional[str]:
    """Get cached symbol resolution."""
    result = await cache_get(f"symbol:{name}")
    if result:
        return result.get("symbol")
    return None
