"""
Redis cache layer for caching PGx lookups and FAERS data.
"""
import redis.asyncio as redis
import json
from src.config import settings
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        client = await get_redis_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
    return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL (default 1 hour)."""
    try:
        client = await get_redis_client()
        await client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    try:
        client = await get_redis_client()
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error for key {key}: {e}")
        return False


async def cache_flush() -> bool:
    """Flush all cache (use with caution!)."""
    try:
        client = await get_redis_client()
        await client.flushdb()
        return True
    except Exception as e:
        logger.warning(f"Cache flush error: {e}")
        return False


class CacheKeyBuilder:
    """Helper for building consistent cache keys."""

    @staticmethod
    def pgx_recommendation(gene: str, drug: str) -> str:
        """Cache key for PGx recommendation."""
        return f"pgx:{gene.lower()}:{drug.lower()}"

    @staticmethod
    def ddi(drug_a: str, drug_b: str) -> str:
        """Cache key for DDI lookup."""
        drugs_sorted = tuple(sorted([drug_a.lower(), drug_b.lower()]))
        return f"ddi:{drugs_sorted[0]}:{drugs_sorted[1]}"

    @staticmethod
    def faers(drug_name: str) -> str:
        """Cache key for FAERS data."""
        return f"faers:{drug_name.lower()}"

    @staticmethod
    def drug(drug_id: int) -> str:
        """Cache key for drug info."""
        return f"drug:{drug_id}"
