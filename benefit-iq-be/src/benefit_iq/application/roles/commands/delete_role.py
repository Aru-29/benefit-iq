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
class DeleteRoleCommand:
    """Class missing docstring."""

    role_id: UUID


class DeleteRoleHandler:
    """Class missing docstring."""

    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        """Function missing docstring."""
        self.repository = repository

    async def handle(
        self,
        command: DeleteRoleCommand,
    ) -> None:
        """Async function missing docstring."""
        role = await self.repository.get_by_id(command.role_id)

        if role is None:
            raise RoleNotFoundException(f"Role '{command.role_id}' was not found.")

        await self.repository.delete(command.role_id)

        logger.info(
            "role_deleted",
            role_id=str(command.role_id),
        )
