import redis
from typing import Optional, Dict, Any
import json
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {str(e)}")
            return None

    def set(self, key: str, value: Dict[str, Any], ttl_hours: int = 24) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = timedelta(hours=ttl_hours)
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Set cache key {key} with TTL {ttl_hours}h")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {str(e)}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            cursor = 0
            count = 0
            keys = []
            
            while True:
                cursor, matches = self.client.scan(cursor, match=pattern)
                keys.extend(matches)
                if cursor == 0:
                    break
            
            if keys:
                count = self.client.delete(*keys)
            
            logger.info(f"Cleared {count} cache keys matching pattern {pattern}")
            return count
        except Exception as e:
            logger.warning(f"Cache clear pattern error: {str(e)}")
            return 0

    def close(self):
        """Close Redis connection"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {str(e)}")


# Global cache instance
cache = None


def get_cache() -> RedisCache:
    """Get or create global Redis cache"""
    global cache
    if cache is None:
        from src.config import REDIS_HOST, REDIS_PORT, REDIS_DB
        cache = RedisCache(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB
        )
    return cache
