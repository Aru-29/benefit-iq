"""
Module missing docstring.
"""

import redis.asyncio as redis

from benefit_iq.infrastructure.configuration.settings import (
    RedisSettings,
)


class RedisCache:
    """Class missing docstring."""

    def __init__(
        self,
        settings: RedisSettings,
    ) -> None:
        """Function missing docstring."""
        self.settings = settings
        self.client: redis.Redis | None = None

    async def connect(self) -> None:
        """Async function missing docstring."""
        if not self.settings.enabled:
            return

        self.client = redis.Redis(
            host=self.settings.host,
            port=self.settings.port,
            password=(self.settings.password or None),
            db=self.settings.database,
            decode_responses=True,
        )

        await self.client.ping()

    async def get(
        self,
        key: str,
    ) -> str | None:
        """Async function missing docstring."""
        if self.client is None:
            return None

        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        """Async function missing docstring."""
        if self.client is None:
            return

        await self.client.set(
            key,
            value,
            ex=ttl,
        )

    async def delete(
        self,
        key: str,
    ) -> None:
        """Async function missing docstring."""
        if self.client is None:
            return

        await self.client.delete(key)

    async def close(self) -> None:
        """Async function missing docstring."""
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    def lock(self, key: str):
        """Fail closed when coordination storage is unavailable."""
        import hashlib

        if self.client is None:
            raise RuntimeError("Redis is required for serialized writes")
        return self.client.lock(
            "benefitiq:lock:" + hashlib.sha256(key.encode()).hexdigest(),
            timeout=120,
            blocking_timeout=10,
        )
