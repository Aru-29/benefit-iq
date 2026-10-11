"""
Module missing docstring.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from benefit_iq.application.contracts.repositories.role_repository import (
    RoleRepository,
)
from benefit_iq.domain.entities.role import Role
from benefit_iq.domain.exceptions.role_exceptions import (
    RoleAlreadyExistsException,
)
from benefit_iq.domain.valueobjects.role_name import RoleName

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CreateRoleCommand:
    """Class missing docstring."""

    name: str
    description: str | None = None


class CreateRoleHandler:
    """Class missing docstring."""

    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        """Function missing docstring."""
        self.repository = repository

    async def handle(
        self,
        command: CreateRoleCommand,
    ) -> Role:
        """Async function missing docstring."""
        role_name = RoleName(command.name)

        existing = await self.repository.get_by_name(role_name.value)

        if existing:
            raise RoleAlreadyExistsException(f"Role '{role_name.value}' already exists.")

        now = datetime.now(UTC)

        role = Role(
            id=uuid4(),
            name=role_name.value,
            description=command.description,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        result = await self.repository.create(role)

        logger.info(
            "role_created",
            role_id=str(result.id),
            role_name=result.name,
        )

        return result
