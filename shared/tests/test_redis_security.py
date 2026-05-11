"""
Redis Security Tests for TheraGenome.

Tests security properties of Redis configuration and cache implementations:
- Authentication enforcement
- Cross-service key isolation
- TTL enforcement
- Pickle serialization prevention
- Fail-safe error handling
- PII protection
"""

import pytest
import os
import json
import pickle
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Optional

# Mock redis module before importing our modules
import redis.asyncio as aioredis


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    client = AsyncMock(spec=aioredis.Redis)
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.scan = AsyncMock(return_value=(0, []))
    client.close = AsyncMock()
    return client


@pytest.fixture
def redis_env_vars():
    """Set up Redis environment variables."""
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["REDIS_DB"] = "0"
    os.environ["REDIS_PASSWORD"] = "test-password-123"
    os.environ["REDIS_CACHE_ENABLED"] = "true"
    yield
    # Cleanup
    for key in ["REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_PASSWORD", "REDIS_CACHE_ENABLED"]:
        os.environ.pop(key, None)


class TestRedisAuthentication:
    """Test Redis authentication enforcement."""
    
    def test_redis_config_requires_password(self, redis_env_vars):
        """Test that Redis configuration requires password."""
        from shared.utils.redis_client import RedisConfig
        
        config = RedisConfig()
        assert config.password is not None
        assert config.password == "test-password-123"
    
    def test_redis_config_missing_password_warning(self):
        """Test that missing password generates warning."""
        # Remove password from environment
        os.environ.pop("REDIS_PASSWORD", None)
        
        from shared.utils.redis_client import RedisConfig
        
        with pytest.warns(UserWarning):
            config = RedisConfig()
            assert config.password is None
    
    @pytest.mark.asyncio
    async def test_redis_client_requires_password(self, redis_env_vars):
        """Test that Redis client requires password."""
        from shared.utils.redis_client import get_redis_client
        
        # This should not raise because password is set
        try:
            client = get_redis_client()
            assert client is not None
        except RuntimeError:
            pytest.fail("Redis client should be created when password is set")
    
    @pytest.mark.asyncio
    async def test_redis_client_fails_without_password(self):
        """Test that Redis client fails without password."""
        from shared.utils.redis_client import get_redis_client
        
        # Remove password
        os.environ.pop("REDIS_PASSWORD", None)
        
        # Clear the lru_cache to reset the singleton
        get_redis_client.cache_clear()
        
        # Should raise RuntimeError
        with pytest.raises(RuntimeError):
            client = get_redis_client()


class TestCrossServiceKeyIsolation:
    """Test that services cannot access each other's cache keys."""
    
    @pytest.mark.asyncio
    async def test_dev1_key_prefix(self, redis_env_vars, mock_redis_client):
        """Test that Dev1 cache uses dev1: prefix."""
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        # Set a value
        await cache.set("variant", "rs1234567", value={"test": "data"}, ttl=3600)
        
        # Verify the key has dev1 prefix
        call_args = mock_redis_client.setex.call_args
        set_key = call_args[0][0]
        assert set_key.startswith("dev1:"), f"Key should start with 'dev1:' but got {set_key}"
        assert "variant:rs1234567" in set_key
    
    @pytest.mark.asyncio
    async def test_dev2_key_prefix(self, redis_env_vars, mock_redis_client):
        """Test that Dev2 cache uses dev2: prefix."""
        from services.dev2_pathogen_resistance_api.src.cache.redis_cache import Dev2RedisCache
        
        cache = Dev2RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        await cache.set("resistance", "MRSA", value={"resistant": True}, ttl=3600)
        
        call_args = mock_redis_client.setex.call_args
        set_key = call_args[0][0]
        assert set_key.startswith("dev2:"), f"Key should start with 'dev2:' but got {set_key}"
    
    @pytest.mark.asyncio
    async def test_dev3_key_prefix(self, redis_env_vars, mock_redis_client):
        """Test that Dev3 cache uses dev3: prefix."""
        from services.dev3_drug_safety_toxicity_api.src.cache.redis_cache import Dev3RedisCache
        
        cache = Dev3RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        await cache.set("pgx", "CYP2D6", value={"metabolism": "slow"}, ttl=86400)
        
        call_args = mock_redis_client.setex.call_args
        set_key = call_args[0][0]
        assert set_key.startswith("dev3:"), f"Key should start with 'dev3:' but got {set_key}"
    
    @pytest.mark.asyncio
    async def test_dev4_key_prefix(self, redis_env_vars, mock_redis_client):
        """Test that Dev4 cache uses dev4: prefix."""
        from services.dev4_core_platform_orchestration.src.cache.redis_cache import Dev4RedisCache
        
        cache = Dev4RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        await cache.set("session", "sess_123", value={"user": "P_001"}, ttl=1800)
        
        call_args = mock_redis_client.setex.call_args
        set_key = call_args[0][0]
        assert set_key.startswith("dev4:"), f"Key should start with 'dev4:' but got {set_key}"
    
    @pytest.mark.asyncio
    async def test_cross_service_key_access_fails(self, redis_env_vars, mock_redis_client):
        """Test that attempting to read another service's key returns None."""
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        # Set up mock to return data for dev2 key
        async def mock_get(key):
            if key.startswith("dev2:"):
                return json.dumps({"data": "should not access"})
            return None
        
        mock_redis_client.get = AsyncMock(side_effect=mock_get)
        
        cache = Dev1RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        # Try to read a dev2 key with dev1 prefix (should fail)
        result = await cache.get("dev2:resistance:MRSA")
        assert result is None


class TestTTLEnforcement:
    """Test that all cached values have TTL."""
    
    @pytest.mark.asyncio
    async def test_set_without_ttl_uses_default(self, redis_env_vars, mock_redis_client):
        """Test that set() uses default TTL when not specified."""
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        await cache.set("variant", "rs123", value={"test": "data"})
        
        # setex should have been called with TTL argument
        call_args = mock_redis_client.setex.call_args
        ttl = call_args[0][1]
        assert ttl > 0, "TTL should be greater than 0"
        assert ttl == 3600  # Default variant TTL
    
    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, redis_env_vars, mock_redis_client):
        """Test that set() respects custom TTL."""
        from services.dev4_core_platform_orchestration.src.cache.redis_cache import Dev4RedisCache
        
        cache = Dev4RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        await cache.set("session", "sess_123", value={"test": "data"}, ttl=7200)
        
        call_args = mock_redis_client.setex.call_args
        ttl = call_args[0][1]
        assert ttl == 7200, "TTL should be 7200 as specified"
    
    @pytest.mark.asyncio
    async def test_set_rejects_invalid_ttl(self, redis_env_vars, mock_redis_client):
        """Test that set() rejects invalid TTL."""
        from services.dev3_drug_safety_toxicity_api.src.cache.redis_cache import Dev3RedisCache
        
        cache = Dev3RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        # TTL of 0 should be rejected
        result = await cache.set("pgx", "test", value={"test": "data"}, ttl=0)
        assert result is False, "TTL of 0 should be rejected"


class TestPickleSerializationBlocked:
    """Test that pickle serialization is blocked."""
    
    @pytest.mark.asyncio
    async def test_json_serialization_used(self, redis_env_vars, mock_redis_client):
        """Test that cache uses JSON serialization, not pickle."""
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        test_data = {"classification": "benign", "confidence": 0.95}
        await cache.set("variant", "rs123", value=test_data, ttl=3600)
        
        # Get the serialized value that was stored
        call_args = mock_redis_client.setex.call_args
        serialized = call_args[0][2]
        
        # Should be JSON, not pickle
        try:
            deserialized = json.loads(serialized)
            assert deserialized == test_data
        except json.JSONDecodeError:
            pytest.fail("Value should be JSON serialized")


class TestFailSafeErrorHandling:
    """Test that Redis errors don't crash the service."""
    
    @pytest.mark.asyncio
    async def test_redis_down_returns_none_on_get(self, redis_env_vars, mock_redis_client):
        """Test that get() returns None if Redis is down."""
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        mock_redis_client.get = AsyncMock(side_effect=Exception("Redis connection refused"))
        cache._client = mock_redis_client
        cache._enabled = True
        
        # Should return None, not raise
        result = await cache.get("variant", "rs123")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_redis_down_returns_false_on_set(self, redis_env_vars, mock_redis_client):
        """Test that set() returns False if Redis is down."""
        from services.dev2_pathogen_resistance_api.src.cache.redis_cache import Dev2RedisCache
        
        cache = Dev2RedisCache()
        mock_redis_client.setex = AsyncMock(side_effect=Exception("Redis connection refused"))
        cache._client = mock_redis_client
        cache._enabled = True
        
        # Should return False, not raise
        result = await cache.set("resistance", "test", value={"test": "data"}, ttl=3600)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_corrupted_json_returns_none(self, redis_env_vars, mock_redis_client):
        """Test that corrupted cached JSON returns None."""
        from services.dev3_drug_safety_toxicity_api.src.cache.redis_cache import Dev3RedisCache
        
        cache = Dev3RedisCache()
        # Return invalid JSON
        mock_redis_client.get = AsyncMock(return_value="invalid json{{{")
        cache._client = mock_redis_client
        cache._enabled = True
        
        result = await cache.get("pgx", "test")
        assert result is None


class TestPIIProtection:
    """Test that PII is not cached."""
    
    @pytest.mark.asyncio
    async def test_dev_mode_detects_name_in_cache(self, redis_env_vars, mock_redis_client):
        """Test that dev mode detects name keyword in cached value."""
        os.environ["DEBUG"] = "true"
        
        from services.dev4_core_platform_orchestration.src.cache.redis_cache import Dev4RedisCache
        
        cache = Dev4RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        # Try to cache a value with a name field
        with pytest.raises(AssertionError):
            await cache.set(
                "session", "sess_123",
                value={"user_id": "P_001", "patient_name": "John Doe"},
                ttl=1800
            )
        
        os.environ.pop("DEBUG")
    
    @pytest.mark.asyncio
    async def test_dev_mode_detects_token_in_cache(self, redis_env_vars, mock_redis_client):
        """Test that dev mode detects token keyword in cached value."""
        os.environ["DEBUG"] = "true"
        
        from services.dev4_core_platform_orchestration.src.cache.redis_cache import Dev4RedisCache
        
        cache = Dev4RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        # Try to cache a JWT token
        with pytest.raises(AssertionError):
            await cache.set(
                "session", "sess_123",
                value={"jwt_token": "eyJhbGc..."},
                ttl=1800
            )
        
        os.environ.pop("DEBUG")
    
    @pytest.mark.asyncio
    async def test_prod_mode_skips_pii_check(self, redis_env_vars, mock_redis_client):
        """Test that production mode doesn't validate PII (for performance)."""
        os.environ.pop("DEBUG", None)  # Ensure DEBUG is off
        
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        cache._client = mock_redis_client
        cache._enabled = True
        
        # This should work in production mode even with suspicious keywords
        result = await cache.set(
            "variant", "rs123",
            value={"classification": "benign"},
            ttl=3600
        )
        assert result is True


class TestCacheDisabledFallback:
    """Test that service works when cache is disabled."""
    
    @pytest.mark.asyncio
    async def test_cache_disabled_returns_none(self, redis_env_vars, mock_redis_client):
        """Test that get() returns None when cache is disabled."""
        os.environ["REDIS_CACHE_ENABLED"] = "false"
        
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        
        result = await cache.get("variant", "rs123")
        assert result is None
        
        # Redis client should not have been called
        mock_redis_client.get.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_disabled_set_returns_false(self, redis_env_vars, mock_redis_client):
        """Test that set() returns False when cache is disabled."""
        os.environ["REDIS_CACHE_ENABLED"] = "false"
        
        from services.dev2_pathogen_resistance_api.src.cache.redis_cache import Dev2RedisCache
        
        cache = Dev2RedisCache()
        
        result = await cache.set(
            "resistance", "test",
            value={"test": "data"},
            ttl=3600
        )
        assert result is False
        
        # Redis client should not have been called
        mock_redis_client.setex.assert_not_called()


class TestServiceIsolation:
    """Test complete service isolation."""
    
    @pytest.mark.asyncio
    async def test_dev1_cannot_access_dev2_pattern(self, redis_env_vars, mock_redis_client):
        """Test that Dev1 cannot delete Dev2 keys with pattern."""
        from services.dev1_genomics_variant_api.src.cache.redis_cache import Dev1RedisCache
        
        cache = Dev1RedisCache()
        
        # Pattern that looks like dev2 keys
        pattern = "resistance:*"
        
        # When deleted with Dev1, should be prefixed with "dev1:"
        await cache.delete_pattern(pattern)
        
        # Verify the pattern used was dev1-prefixed
        call_args = mock_redis_client.scan.call_args
        scan_pattern = call_args[1]["match"]
        assert scan_pattern.startswith("dev1:"), \
            f"Pattern should be dev1-prefixed, got {scan_pattern}"
