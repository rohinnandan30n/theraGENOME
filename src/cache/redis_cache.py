"""
Resilient cache layer with Redis fallback to in-memory caching.

Provides abstract CacheBackend interface with two implementations:
1. RedisCache - Uses Redis for distributed caching
2. InMemoryCache - Fallback for when Redis is unavailable

The factory function get_cache() automatically selects the appropriate
backend based on Redis availability.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Get value from cache. Returns None if key doesn't exist."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class RedisCache(CacheBackend):
    """Redis-backed cache implementation."""
    
    def __init__(self, url: str = None):
        """
        Initialize Redis cache.
        
        Args:
            url: Redis connection URL (default: REDIS_URL env var or redis://localhost:6379/0)
            
        Raises:
            ConnectionError: If Redis is unreachable
        """
        self.url = url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            import redis
            self.client = redis.from_url(self.url, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info(f"Redis connection established: {self.url.split('@')[-1]}")
        except ImportError:
            logger.error("redis module not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {self.url}: {str(e)}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis cache."""
        try:
            value = self.client.get(key)
            return value
        except Exception as e:
            logger.warning(f"Redis get error for key '{key}': {str(e)}")
            return None
    
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set value in Redis cache with TTL."""
        try:
            if ttl_seconds > 0:
                self.client.setex(key, ttl_seconds, value)
            else:
                self.client.set(key, value)
            logger.debug(f"Set Redis key '{key}' (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.warning(f"Redis set error for key '{key}': {str(e)}")
    
    def delete(self, key: str) -> None:
        """Delete key from Redis cache."""
        try:
            self.client.delete(key)
            logger.debug(f"Deleted Redis key '{key}'")
        except Exception as e:
            logger.warning(f"Redis delete error for key '{key}': {str(e)}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis exists error for key '{key}': {str(e)}")
            return False


class InMemoryCache(CacheBackend):
    """In-memory cache with expiry tracking."""
    
    def __init__(self):
        """Initialize in-memory cache."""
        self.store: Dict[str, Dict[str, Any]] = {}
        logger.info("In-memory cache initialized")
    
    def get(self, key: str) -> Optional[str]:
        """Get value from in-memory cache, checking expiry."""
        if key not in self.store:
            return None
        
        entry = self.store[key]
        
        # Check if expired
        if entry.get('expires_at') and datetime.utcnow() > entry['expires_at']:
            del self.store[key]
            return None
        
        return entry.get('value')
    
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Set value in in-memory cache with optional TTL."""
        expires_at = None
        if ttl_seconds > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        self.store[key] = {
            'value': value,
            'expires_at': expires_at,
            'set_at': datetime.utcnow()
        }
        logger.debug(f"Set in-memory key '{key}' (TTL: {ttl_seconds}s)")
    
    def delete(self, key: str) -> None:
        """Delete key from in-memory cache."""
        if key in self.store:
            del self.store[key]
            logger.debug(f"Deleted in-memory key '{key}'")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in in-memory cache."""
        if key not in self.store:
            return False
        
        entry = self.store[key]
        
        # Check if expired
        if entry.get('expires_at') and datetime.utcnow() > entry['expires_at']:
            del self.store[key]
            return False
        
        return True


# Global cache instance
_cache_instance: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """
    Get or create global cache instance with Redis fallback.
    
    Try to connect to Redis first. If unavailable (import error or
    connection error), fall back to in-memory caching.
    
    Returns:
        CacheBackend: Either RedisCache or InMemoryCache instance
    """
    global _cache_instance
    
    if _cache_instance is not None:
        return _cache_instance
    
    # Try Redis first
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _cache_instance = RedisCache(url=redis_url)
        return _cache_instance
    except ImportError:
        logger.warning("Redis module not available. Using in-memory cache.")
    except Exception as e:
        logger.warning(f"Redis unavailable ({str(e)}). Using in-memory cache.")
    
    # Fallback to in-memory cache
    _cache_instance = InMemoryCache()
    return _cache_instance


# For backwards compatibility, keep the old interface
def create_cache() -> CacheBackend:
    """Alias for get_cache() for backwards compatibility."""
    return get_cache()


# Legacy RedisCache wrapper for code that uses it directly
class _LegacyRedisCache:
    """Legacy interface for code that expects the old RedisCache behavior."""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """Initialize using factory function."""
        self._cache = get_cache()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache (dict-compatible)."""
        try:
            value = self._cache.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl_hours: int = 24) -> bool:
        """Set value in cache with TTL in hours."""
        try:
            ttl_seconds = ttl_hours * 3600
            self._cache.set(key, json.dumps(value), ttl_seconds)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            self._cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if isinstance(self._cache, InMemoryCache):
            # For in-memory cache, do simple pattern matching
            import fnmatch
            count = 0
            keys_to_delete = []
            for key in self._cache.store.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                self._cache.delete(key)
            return len(keys_to_delete)
        elif isinstance(self._cache, RedisCache):
            # For Redis cache, use SCAN
            try:
                cursor = 0
                count = 0
                keys = []
                
                while True:
                    cursor, matches = self._cache.client.scan(cursor, match=pattern)
                    keys.extend(matches)
                    if cursor == 0:
                        break
                
                if keys:
                    count = self._cache.client.delete(*keys)
                
                logger.info(f"Cleared {count} cache keys matching pattern {pattern}")
                return count
            except Exception as e:
                logger.warning(f"Cache clear pattern error: {str(e)}")
                return 0
        return 0
    
    def close(self):
        """Close cache connection (no-op for in-memory cache)."""
        if isinstance(self._cache, RedisCache):
            try:
                self._cache.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {str(e)}")

