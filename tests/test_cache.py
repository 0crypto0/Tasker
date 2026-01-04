"""Cache layer tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache import CacheService


class TestCacheService:
    """Tests for cache service."""

    @pytest.fixture
    def cache_service(self) -> CacheService:
        """Create a cache service instance for testing."""
        return CacheService()

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_connected(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test get returns None when Redis is not connected."""
        result = await cache_service.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_returns_false_when_not_connected(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test set returns False when Redis is not connected."""
        result = await cache_service.set("test_key", "test_value")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_not_connected(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test delete returns False when Redis is not connected."""
        result = await cache_service.delete("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_not_connected(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test exists returns False when Redis is not connected."""
        result = await cache_service.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_make_key_adds_prefix(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that _make_key adds the correct prefix."""
        key = cache_service._make_key("test_key")
        assert key == "tasker:test_key"

    @pytest.mark.asyncio
    async def test_get_parses_json(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that get parses JSON values."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"key": "value"}'
        cache_service._redis = mock_redis

        result = await cache_service.get("test_key")

        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("tasker:test_key")

    @pytest.mark.asyncio
    async def test_get_returns_string_for_non_json(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that get returns string for non-JSON values."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "plain_string"
        cache_service._redis = mock_redis

        result = await cache_service.get("test_key")

        assert result == "plain_string"

    @pytest.mark.asyncio
    async def test_set_serializes_dict(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that set serializes dict values to JSON."""
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis

        await cache_service.set("test_key", {"key": "value"}, ttl=3600)

        mock_redis.setex.assert_called_once_with(
            "tasker:test_key",
            3600,
            '{"key": "value"}',
        )

    @pytest.mark.asyncio
    async def test_set_uses_default_ttl(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that set uses default TTL when not specified."""
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis

        with patch("app.core.cache.settings") as mock_settings:
            mock_settings.cache_ttl_seconds = 7200

            await cache_service.set("test_key", "value")

            mock_redis.setex.assert_called_once_with(
                "tasker:test_key",
                7200,
                "value",
            )

    @pytest.mark.asyncio
    async def test_delete_returns_true_on_success(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that delete returns True when key is deleted."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        cache_service._redis = mock_redis

        result = await cache_service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("tasker:test_key")

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_key_not_exists(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that delete returns False when key doesn't exist."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 0
        cache_service._redis = mock_redis

        result = await cache_service.delete("test_key")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_task_output(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test get_task_output method."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"status": "completed"}'
        cache_service._redis = mock_redis

        result = await cache_service.get_task_output("uuid-123")

        assert result == {"status": "completed"}
        mock_redis.get.assert_called_once_with("tasker:task_output:uuid-123")

    @pytest.mark.asyncio
    async def test_set_task_output(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test set_task_output method."""
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis

        with patch("app.core.cache.settings") as mock_settings:
            mock_settings.cache_ttl_seconds = 3600

            await cache_service.set_task_output(
                "uuid-123",
                {"status": "completed"},
            )

            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert "tasker:task_output:uuid-123" in call_args[0]

    @pytest.mark.asyncio
    async def test_invalidate_task_output(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test invalidate_task_output method."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        cache_service._redis = mock_redis

        result = await cache_service.invalidate_task_output("uuid-123")

        assert result is True
        mock_redis.delete.assert_called_once_with("tasker:task_output:uuid-123")

    @pytest.mark.asyncio
    async def test_connect_creates_redis_client(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that connect creates a Redis client."""
        with patch("app.core.cache.redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            await cache_service.connect()

            assert cache_service._redis == mock_client

    @pytest.mark.asyncio
    async def test_disconnect_closes_redis_client(
        self,
        cache_service: CacheService,
    ) -> None:
        """Test that disconnect closes the Redis client."""
        mock_redis = AsyncMock()
        cache_service._redis = mock_redis

        await cache_service.disconnect()

        mock_redis.close.assert_called_once()
        assert cache_service._redis is None


class TestCacheMetrics:
    """Tests for cache metrics."""

    @pytest.mark.asyncio
    async def test_cache_hit_increments_counter(self) -> None:
        """Test that cache hit increments the counter."""
        cache_service = CacheService()
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"key": "value"}'
        cache_service._redis = mock_redis

        with patch("app.core.cache.cache_hits_counter") as mock_counter:
            await cache_service.get("test_key")
            mock_counter.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_increments_counter(self) -> None:
        """Test that cache miss increments the counter."""
        cache_service = CacheService()
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        cache_service._redis = mock_redis

        with patch("app.core.cache.cache_misses_counter") as mock_counter:
            await cache_service.get("test_key")
            mock_counter.inc.assert_called_once()

