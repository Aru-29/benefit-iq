"""
Module missing docstring.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
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
class DeactivateRoleCommand:
    """Class missing docstring."""

    role_id: UUID


class DeactivateRoleHandler:
    """Class missing docstring."""

    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        """Function missing docstring."""
        self.repository = repository

    async def handle(
        self,
        command: DeactivateRoleCommand,
    ):
        """Async function missing docstring."""
        role = await self.repository.get_by_id(command.role_id)

        if role is None:
            raise RoleNotFoundException(f"Role '{command.role_id}' was not found.")

        role.deactivate()
        role.updated_at = datetime.now(UTC)

        result = await self.repository.update(role)

        logger.info(
            "role_deactivated",
            role_id=str(result.id),
        )

        return result
