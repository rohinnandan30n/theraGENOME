"""
Unit tests for Redis cache layer.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.cache.redis_cache import (
    cache_get,
    cache_set,
    cache_delete,
    CacheKeyBuilder,
)


class TestCacheKeyBuilder:
    """Test suite for cache key generation."""

    def test_pgx_recommendation_key(self):
        """Test PGx recommendation cache key format."""
        key = CacheKeyBuilder.pgx_recommendation("CYP2C9", "warfarin")
        assert key == "pgx:cyp2c9:warfarin"

    def test_pgx_recommendation_case_insensitive(self):
        """Test PGx key is case-insensitive."""
        key1 = CacheKeyBuilder.pgx_recommendation("CYP2C9", "Warfarin")
        key2 = CacheKeyBuilder.pgx_recommendation("cyp2c9", "warfarin")
        assert key1 == key2

    def test_ddi_key_order_independent(self):
        """Test DDI key is order-independent."""
        key1 = CacheKeyBuilder.ddi("warfarin", "aspirin")
        key2 = CacheKeyBuilder.ddi("aspirin", "warfarin")
        assert key1 == key2

    def test_ddi_key_format(self):
        """Test DDI cache key format."""
        key = CacheKeyBuilder.ddi("warfarin", "aspirin")
        assert key.startswith("ddi:")
        assert "aspirin" in key
        assert "warfarin" in key

    def test_faers_key(self):
        """Test FAERS cache key format."""
        key = CacheKeyBuilder.faers("aspirin")
        assert key == "faers:aspirin"

    def test_drug_key(self):
        """Test drug cache key format."""
        key = CacheKeyBuilder.drug(123)
        assert key == "drug:123"


class TestCacheOperations:
    """Test suite for cache get/set/delete operations."""

    @pytest.mark.asyncio
    async def test_cache_get_nonexistent_key(self):
        """Test getting non-existent key returns None."""
        with patch("src.cache.redis_cache.get_redis_client") as mock_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_client.return_value = mock_redis

            result = await cache_get("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cache value."""
        test_data = {"gene": "CYP2C9", "drug": "warfarin"}

        with patch("src.cache.redis_cache.get_redis_client") as mock_client:
            mock_redis = AsyncMock()
            mock_client.return_value = mock_redis

            # Set
            await cache_set("test_key", test_data)
            mock_redis.setex.assert_called_once()

            # Get
            mock_redis.get.return_value = json.dumps(test_data)
            result = await cache_get("test_key")
            assert result == test_data

    @pytest.mark.asyncio
    async def test_cache_set_with_ttl(self):
        """Test cache set respects TTL."""
        with patch("src.cache.redis_cache.get_redis_client") as mock_client:
            mock_redis = AsyncMock()
            mock_client.return_value = mock_redis

            await cache_set("test_key", {"data": "value"}, ttl=7200)

            # Verify setex was called with proper TTL
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 7200  # TTL argument

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test cache delete removes key."""
        with patch("src.cache.redis_cache.get_redis_client") as mock_client:
            mock_redis = AsyncMock()
            mock_client.return_value = mock_redis

            result = await cache_delete("test_key")
            mock_redis.delete.assert_called_once_with("test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_cache_get_on_error(self):
        """Test cache get handles errors gracefully."""
        with patch("src.cache.redis_cache.get_redis_client") as mock_client:
            mock_redis = AsyncMock()
            mock_redis.get.side_effect = Exception("Connection error")
            mock_client.return_value = mock_redis

            result = await cache_get("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_on_error(self):
        """Test cache set handles errors gracefully."""
        with patch("src.cache.redis_cache.get_redis_client") as mock_client:
            mock_redis = AsyncMock()
            mock_redis.setex.side_effect = Exception("Connection error")
            mock_client.return_value = mock_redis

            result = await cache_set("test_key", {"data": "value"})
            assert result is False
