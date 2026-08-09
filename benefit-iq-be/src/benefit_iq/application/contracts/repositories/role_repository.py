"""
Module missing docstring.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from benefit_iq.domain.entities.role import Role


class RoleRepository(ABC):
    """Class missing docstring."""

    @abstractmethod
    async def create(self, role: Role) -> Role:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def get_by_id(
        self,
        role_id: UUID,
    ) -> Role | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def list(
        self,
        offset: int,
        limit: int,
    ) -> list[Role]:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def update(
        self,
        role: Role,
    ) -> Role:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def delete(
        self,
        role_id: UUID,
    ) -> None:
        """Async function missing docstring."""
        ...
