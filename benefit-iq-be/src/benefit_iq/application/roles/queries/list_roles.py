"""
Module missing docstring.
"""

from dataclasses import dataclass

import structlog

from benefit_iq.application.contracts.repositories.role_repository import (
    RoleRepository,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ListRolesQuery:
    """Class missing docstring."""

    page: int = 1
    page_size: int = 20


class ListRolesHandler:
    """Class missing docstring."""

    def __init__(
        self,
        repository: RoleRepository,
    ) -> None:
        """Function missing docstring."""
        self.repository = repository

    async def handle(
        self,
        query: ListRolesQuery,
    ):
        """Async function missing docstring."""
        offset = (query.page - 1) * query.page_size
        limit = query.page_size

        return await self.repository.list(
            offset=offset,
            limit=limit,
        )
