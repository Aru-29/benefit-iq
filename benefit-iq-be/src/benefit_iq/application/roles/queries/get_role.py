"""
Module missing docstring.
"""

from dataclasses import dataclass
from uuid import UUID

import structlog

from benefit_iq.application.contracts.repositories.role_repository import (
    RoleRepository,
)
from benefit_iq.domain.exceptions.role_exceptions import (
    RoleNotFoundException,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class GetRoleQuery:
    """Class missing docstring."""

    role_id: UUID


class GetRoleHandler:
    """Class missing docstring."""

    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        """Function missing docstring."""
        self.repository = repository

    async def handle(
        self,
        query: GetRoleQuery,
    ):
        """Async function missing docstring."""
        role = await self.repository.get_by_id(query.role_id)

        if role is None:
            raise RoleNotFoundException(f"Role '{query.role_id}' was not found.")

        return role
