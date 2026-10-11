"""
Module missing docstring.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from benefit_iq.domain.entities.user import User


class UserRepository(ABC):
    """Class missing docstring."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def get_by_external_id(self, provider: str, external_id: str) -> User | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def list(self, offset: int, limit: int) -> list[User]:
        """Lists users with pagination."""
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Deactivates/deletes a user entity by ID."""
        ...
