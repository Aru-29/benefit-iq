"""
Module missing docstring.
"""

from abc import ABC, abstractmethod


class CacheService(ABC):
    """Class missing docstring."""

    @abstractmethod
    async def get(
        self,
        key: str,
    ) -> str | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def delete(
        self,
        key: str,
    ) -> None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Async function missing docstring."""
        ...
