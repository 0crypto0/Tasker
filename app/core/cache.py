"""Redis cache layer implementation."""

import json
from typing import Any

import redis.asyncio as redis

from app.config import get_settings
from app.core.metrics import cache_hits_counter, cache_misses_counter

settings = get_settings()


class CacheService:
    """Redis cache service with TTL and metrics."""

    def __init__(self) -> None:
        """Initialize cache service."""
        self._redis: redis.Redis | None = None
        self._prefix = "tasker:"

    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._redis:
            return None

        full_key = self._make_key(key)
        value = await self._redis.get(full_key)

        if value is not None:
            cache_hits_counter.inc()
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            cache_misses_counter.inc()
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (defaults to settings.cache_ttl_seconds)

        Returns:
            True if successful
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        ttl = ttl or settings.cache_ttl_seconds

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        await self._redis.setex(full_key, ttl, value)
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        result = await self._redis.delete(full_key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self._redis:
            return False

        full_key = self._make_key(key)
        return await self._redis.exists(full_key) > 0

    async def get_task_output(self, task_uuid: str) -> dict[str, Any] | None:
        """Get task output from cache.

        Args:
            task_uuid: Task UUID

        Returns:
            Task output or None if not cached
        """
        return await self.get(f"task_output:{task_uuid}")

    async def set_task_output(
        self,
        task_uuid: str,
        output: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """Cache task output.

        Args:
            task_uuid: Task UUID
            output: Task output to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        return await self.set(f"task_output:{task_uuid}", output, ttl)

    async def invalidate_task_output(self, task_uuid: str) -> bool:
        """Invalidate cached task output.

        Args:
            task_uuid: Task UUID

        Returns:
            True if cache was invalidated
        """
        return await self.delete(f"task_output:{task_uuid}")


# Global cache service instance
cache_service = CacheService()


async def get_cache() -> CacheService:
    """Dependency for getting cache service."""
    return cache_service

