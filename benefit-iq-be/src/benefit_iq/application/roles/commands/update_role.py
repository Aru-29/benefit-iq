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
    RoleAlreadyExistsException,
    RoleNotFoundException,
)
from benefit_iq.domain.valueobjects.role_name import RoleName


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class UpdateRoleCommand:
    """Class missing docstring."""
    role_id: UUID
    name: str
    description: str | None
    is_active: bool


class UpdateRoleHandler:

    """Class missing docstring."""
    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        """Function missing docstring."""
        self.repository = repository

    async def handle(
        self,
        command: UpdateRoleCommand,
    ):

        """Async function missing docstring."""
        role = await self.repository.get_by_id(
            command.role_id
        )

        if role is None:
            raise RoleNotFoundException(
                f"Role '{command.role_id}' was not found."
            )

        role_name = RoleName(command.name)

        existing = await self.repository.get_by_name(
            role_name.value
        )

        if existing and existing.id != role.id:
            raise RoleAlreadyExistsException(
                f"Role '{role_name.value}' already exists."
            )

        role.update(
            name=role_name.value,
            description=command.description,
        )

        if command.is_active:
            role.activate()
        else:
            role.deactivate()

        role.updated_at = datetime.now(UTC)

        result = await self.repository.update(role)

        logger.info(
            "role_updated",
            role_id=str(result.id),
        )

        return result
