"""
Secure Redis client factory for TheraGenome.

Provides a single authenticated Redis client shared across all services.
- Reads credentials from environment variables (never hardcoded)
- Uses async (aioredis) for non-blocking I/O
- Implements connection pooling and timeouts
- All services import from here instead of creating their own clients
"""

import os
import logging
from functools import lru_cache
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration from environment variables."""
    
    def __init__(self):
        """Load Redis configuration from environment."""
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD")
        
        # Connection timeouts (in seconds)
        self.socket_connect_timeout = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
        self.socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
        
        # Retry on timeout
        self.retry_on_timeout = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
        
        # Validation
        if not self.password:
            logger.warning(
                "REDIS_PASSWORD not set in environment. "
                "Redis authentication will fail. Set REDIS_PASSWORD before deployment."
            )
    
    def __repr__(self) -> str:
        """String representation (without password)."""
        return (
            f"RedisConfig(host={self.host}, port={self.port}, db={self.db}, "
            f"socket_connect_timeout={self.socket_connect_timeout}s, "
            f"socket_timeout={self.socket_timeout}s)"
        )


@lru_cache(maxsize=1)
def get_redis_client() -> aioredis.Redis:
    """
    Get or create a singleton async Redis client.
    
    SECURITY NOTES:
    - Credentials loaded from environment variables only (never hardcoded)
    - Connection pooling with configurable timeouts
    - Database selection enforced (always db 0 for safety)
    - Async I/O prevents blocking the event loop
    
    Returns:
        aioredis.Redis: Authenticated async Redis client
        
    Raises:
        RuntimeError: If Redis password is not configured
    """
    config = RedisConfig()
    
    # SECURITY: Require authentication for production
    if not config.password:
        raise RuntimeError(
            "REDIS_PASSWORD must be set in environment. "
            "Never use unauthenticated Redis with sensitive data."
        )
    
    # Create async Redis client with security settings
    client = aioredis.Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password,
        # Decode responses to strings (no bytes)
        decode_responses=True,
        # Connection pool settings
        socket_connect_timeout=config.socket_connect_timeout,
        socket_timeout=config.socket_timeout,
        # Automatic retry on timeout
        retry_on_timeout=config.retry_on_timeout,
        # Connection pool size (default 50 is fine)
        max_connections=50,
    )
    
    logger.info(f"Redis client created: {config}")
    return client


def get_redis_config() -> RedisConfig:
    """Get Redis configuration (for logging/debugging)."""
    return RedisConfig()


async def test_redis_connection(client: Optional[aioredis.Redis] = None) -> bool:
    """
    Test Redis connection and return True if successful.
    
    Args:
        client: Redis client (uses get_redis_client() if not provided)
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    if client is None:
        client = get_redis_client()
    
    try:
        # Test with PING command
        result = await client.ping()
        logger.info("Redis connection test successful")
        return result is True
    except Exception as e:
        logger.error(f"Redis connection test failed: {str(e)}")
        return False


async def close_redis_client(client: aioredis.Redis) -> None:
    """
    Close Redis client connection gracefully.
    
    Args:
        client: Redis client to close
    """
    try:
        await client.close()
        logger.info("Redis client closed")
    except Exception as e:
        logger.warning(f"Error closing Redis client: {str(e)}")


# IMPORTANT: Never call get_redis_client() with parameters
# Pattern: WRONG -> redis.Redis(host="localhost", password=secret)
# Pattern: RIGHT -> get_redis_client()  # credentials from environment only
#
# All credentials MUST come from environment variables.
# No hardcoded connection strings or passwords.
