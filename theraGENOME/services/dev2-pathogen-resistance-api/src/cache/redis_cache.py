"""
Secure Redis cache for Dev2 - Pathogen Resistance API.

Security Rules:
1. Key prefix: "dev2:" (prevents cross-service cache poisoning)
2. TTL enforcement: All keys must have explicit TTL
3. Serialization: JSON only (no pickle)
4. Fail-safe: All Redis errors logged, never raised
5. PII protection: No full patient objects cached
"""

import json
import logging
import os
from typing import Optional, Dict, Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Import shared Redis client factory
from shared.utils.redis_client import get_redis_client

# Service identifier (used in all cache key prefixes)
SERVICE_ID = "dev2"

# Default TTL values (in seconds)
DEFAULT_RESISTANCE_TTL = 3600  # 1 hour for resistance predictions


class Dev2RedisCache:
    """
    Secure Redis cache for Dev2 - Pathogen Resistance API.
    
    SECURITY RULES:
    - All keys prefixed with "dev2:" to prevent cross-service poisoning
    - TTL required on all cached items (cache misses are safe)
    - JSON serialization only (no pickle remote code execution)
    - All Redis errors are caught and logged (fail-safe)
    - PII validation: never cache full patient objects
    
    USAGE PATTERNS:
    1. Resistance prediction:
       key = "dev2:resistance:{pathogen_id}:{drug}"
       value = { "resistant": false, "confidence": 0.98 }
       ttl = 3600
    """
    
    def __init__(self):
        """Initialize Redis connection (async, created on first use)."""
        self._client: Optional[aioredis.Redis] = None
        self._enabled = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
    
    async def _get_client(self) -> aioredis.Redis:
        """Lazy-load Redis client."""
        if self._client is None:
            try:
                self._client = get_redis_client()
                if not await self._client.ping():
                    raise RuntimeError("Redis ping failed")
                logger.info("Dev2 Redis cache connected")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self._enabled = False
                raise
        return self._client
    
    def _build_key(self, *parts: str) -> str:
        """Build cache key with service prefix."""
        all_parts = (SERVICE_ID,) + tuple(str(p) for p in parts)
        return ":".join(all_parts)
    
    async def get(self, *key_parts: str) -> Optional[Dict[str, Any]]:
        """Get value from cache (returns None on miss or error)."""
        if not self._enabled:
            return None
        
        try:
            key = self._build_key(*key_parts)
            client = await self._get_client()
            
            value_str = await client.get(key)
            if value_str is None:
                return None
            
            value = json.loads(value_str)
            logger.debug(f"Cache hit: {key}")
            return value
            
        except json.JSONDecodeError as e:
            logger.warning(f"Cache value corrupted (JSON decode error): {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {str(e)}")
            return None
    
    async def set(
        self,
        *key_parts: str,
        value: Dict[str, Any],
        ttl: int = DEFAULT_RESISTANCE_TTL
    ) -> bool:
        """Set value in cache with TTL."""
        if not self._enabled:
            return False
        
        try:
            # Validate TTL
            if ttl <= 0:
                logger.warning(f"Invalid TTL {ttl}, must be > 0")
                return False
            
            if ttl > 86400 * 365:  # More than 1 year
                logger.warning(
                    f"Suspiciously long TTL {ttl}s for cache key. "
                    f"Something may be wrong in caller."
                )
            
            # Validate value
            self._validate_cache_value(value)
            
            key = self._build_key(*key_parts)
            client = await self._get_client()
            
            value_str = json.dumps(value)
            await client.setex(key, ttl, value_str)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.warning(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, *key_parts: str) -> bool:
        """Delete key from cache."""
        if not self._enabled:
            return False
        
        try:
            key = self._build_key(*key_parts)
            client = await self._get_client()
            
            result = await client.delete(key)
            logger.debug(f"Cache invalidated: {key}")
            return result > 0
            
        except Exception as e:
            logger.warning(f"Cache delete error: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (with service prefix)."""
        if not self._enabled:
            return 0
        
        try:
            full_pattern = self._build_key(pattern)
            client = await self._get_client()
            
            cursor = 0
            keys_to_delete = []
            
            while True:
                cursor, matches = await client.scan(cursor, match=full_pattern)
                keys_to_delete.extend(matches)
                if cursor == 0:
                    break
            
            if keys_to_delete:
                count = await client.delete(*keys_to_delete)
                logger.info(f"Cache pattern delete: {full_pattern} ({count} keys)")
                return count
            
            return 0
            
        except Exception as e:
            logger.warning(f"Cache pattern delete error: {str(e)}")
            return 0
    
    def _validate_cache_value(self, value: Dict[str, Any]) -> None:
        """Validate cached value doesn't contain PII."""
        if not os.getenv("DEBUG", "false").lower() == "true":
            return
        
        pii_keywords = [
            "name", "patient_name", "full_name",
            "phone", "contact", "email", "address",
            "dob", "date_of_birth", "ssn",
            "id_number", "passport",
        ]
        
        value_str = json.dumps(value).lower()
        for keyword in pii_keywords:
            assert keyword not in value_str, (
                f"Cache value contains suspicious PII keyword: {keyword}. "
                f"Never cache full patient objects."
            )
    
    async def close(self) -> None:
        """Close Redis connection gracefully."""
        if self._client:
            try:
                await self._client.close()
                logger.info("Dev2 Redis cache connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {str(e)}")


# Singleton instance for this service
_cache_instance: Optional[Dev2RedisCache] = None


async def get_cache() -> Dev2RedisCache:
    """Get or create singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Dev2RedisCache()
    return _cache_instance
