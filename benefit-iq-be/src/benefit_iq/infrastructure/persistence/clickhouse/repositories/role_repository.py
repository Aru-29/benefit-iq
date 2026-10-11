"""
Role repository implementation for ClickHouse.
"""

from uuid import UUID

import structlog

from benefit_iq.application.contracts.repositories.role_repository import (
    RoleRepository,
)
from benefit_iq.domain.entities.role import Role

logger = structlog.get_logger(__name__)


class ClickHouseRoleRepository(RoleRepository):
    """
    ClickHouse implementation of the RoleRepository interface.
    """

    def __init__(
        self,
        database,
    ) -> None:
        self.database = database

    async def create(
        self,
        role: Role,
    ) -> Role:

        self.database.client.insert(
            "roles",
            [
                [
                    role.id,
                    role.name,
                    role.description,
                    role.is_active,
                    role.created_at,
                    role.updated_at,
                ]
            ],
            column_names=[
                "id",
                "name",
                "description",
                "is_active",
                "created_at",
                "updated_at",
            ],
        )

        return role

    async def get_by_id(
        self,
        role_id: UUID,
    ) -> Role | None:

        query = """
        SELECT
            id,
            name,
            description,
            is_active,
            created_at,
            updated_at
        FROM roles FINAL
        WHERE id = %(role_id)s
        LIMIT 1
        """

        result = self.database.client.query(
            query,
            parameters={
                "role_id": str(role_id),
            },
        )

        if not result.result_rows:
            return None

        return self._to_domain(result.result_rows[0])

    async def get_by_name(
        self,
        name: str,
    ) -> Role | None:

        query = """
        SELECT
            id,
            name,
            description,
            is_active,
            created_at,
            updated_at
        FROM roles FINAL
        WHERE name = %(name)s
        LIMIT 1
        """

        result = self.database.client.query(
            query,
            parameters={
                "name": name,
            },
        )

        if not result.result_rows:
            return None

        return self._to_domain(result.result_rows[0])

    async def list(
        self,
        offset: int,
        limit: int,
    ) -> list[Role]:

        query = """
        SELECT
            id,
            name,
            description,
            is_active,
            created_at,
            updated_at
        FROM roles FINAL
        ORDER BY name
        LIMIT %(limit)s
        OFFSET %(offset)s
        """

        result = self.database.client.query(
            query,
            parameters={
                "limit": limit,
                "offset": offset,
            },
        )

        return [self._to_domain(row) for row in result.result_rows]

    async def update(
        self,
        role: Role,
    ) -> Role:

        self.database.client.insert(
            "roles",
            [
                [
                    role.id,
                    role.name,
                    role.description,
                    role.is_active,
                    role.created_at,
                    role.updated_at,
                ]
            ],
            column_names=[
                "id",
                "name",
                "description",
                "is_active",
                "created_at",
                "updated_at",
            ],
        )

        return role

    async def delete(
        self,
        role_id: UUID,
    ) -> None:

        # Intentionally not implemented as physical deletion.
        # BenefitIQ should prefer deactivation/versioning.
        raise NotImplementedError("Use deactivate instead of physical delete.")

    @staticmethod
    def _to_domain(
        row: tuple,
    ) -> Role:

        (
            role_id,
            name,
            description,
            is_active,
            created_at,
            updated_at,
        ) = row

        return Role(
            id=role_id,
            name=name,
            description=description,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at,
        )
