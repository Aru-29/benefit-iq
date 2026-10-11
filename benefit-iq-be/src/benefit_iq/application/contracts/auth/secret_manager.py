"""
Module missing docstring.
"""

from abc import ABC, abstractmethod


class SecretManager(ABC):
    """Class missing docstring."""

    @abstractmethod
    async def get_secret(self, path: str, key: str) -> str:
        """Retrieves a specific key from a secret path."""
        ...

    @abstractmethod
    async def get_secrets(self, path: str) -> dict[str, str]:
        """Retrieves all keys for a specific secret path."""
        ...

    @abstractmethod
    async def set_secret(self, path: str, secrets: dict[str, str]) -> None:
        """Stores a dictionary of secrets at the specified path."""
        ...
