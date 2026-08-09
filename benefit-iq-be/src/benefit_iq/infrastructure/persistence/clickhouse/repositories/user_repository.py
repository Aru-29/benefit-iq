"""User repository implementation for ClickHouse."""
import asyncio
from datetime import datetime, timezone
import json
from uuid import UUID

from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.enums.auth_provider import AuthProvider
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase


class ClickHouseUserRepository(UserRepository):
    """
    ClickHouse implementation of the UserRepository interface.
    """

    def __init__(self, database: ClickHouseDatabase) -> None:
        """Function missing docstring."""
        self.db = database

    def _map_row_to_user(self, row: tuple) -> User:
        """Function missing docstring."""
        return User(
            id=row[0],
            username=row[1],
            first_name=row[2],
            middle_name=row[3] if row[3] else None,
            last_name=row[4],
            email=row[5],
            password_hash=row[6] if row[6] else None,
            role_id=row[7],
            authentication_provider=AuthProvider(row[8]),
            external_provider_id=row[9] if row[9] else None,
            is_active=bool(row[10]),
            is_email_verified=bool(row[11]),
            preferred_settings=json.loads(row[12]) if row[12] else None,
            created_at=row[13],
            updated_at=row[14],
            last_login_at=row[15] if row[15] else None,
        )

    async def create(self, user: User) -> User:
        """Async function missing docstring."""
        data = [[
            str(user.id),
            user.username,
            user.first_name,
            user.middle_name or "",
            user.last_name,
            user.email,
            user.password_hash or "",
            str(user.role_id),
            user.authentication_provider.value,
            user.external_provider_id or "",
            1 if user.is_active else 0,
            1 if user.is_email_verified else 0,
            json.dumps(user.preferred_settings) if user.preferred_settings else "",
            user.created_at,
            user.updated_at,
            user.last_login_at or __import__('datetime').datetime(2000, 1, 1)
        ]]
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "users",
                data,
                column_names=[
                    "id",
                    "username",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "email",
                    "password_hash",
                    "role_id",
                    "authentication_provider",
                    "external_provider_id",
                    "is_active",
                    "is_email_verified",
                    "preferred_settings",
                    "created_at",
                    "updated_at",
                    "last_login_at",
                ]
            )
        )
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Async function missing docstring."""
        query = "SELECT * FROM benefitiq.users FINAL WHERE id = %(id)s"
        result = await self.db.query_async(query, {"id": str(user_id)})
        if not result.result_rows:
            return None
        return self._map_row_to_user(result.result_rows[0])

    async def get_by_email(self, email: str) -> User | None:
        """Async function missing docstring."""
        query = "SELECT * FROM benefitiq.users FINAL WHERE email = %(email)s"
        result = await self.db.query_async(query, {"email": email})
        if not result.result_rows:
            return None
        return self._map_row_to_user(result.result_rows[0])

    async def get_by_username(self, username: str) -> User | None:
        """Async function missing docstring."""
        query = "SELECT * FROM benefitiq.users FINAL WHERE username = %(username)s"
        result = await self.db.query_async(query, {"username": username})
        if not result.result_rows:
            return None
        return self._map_row_to_user(result.result_rows[0])

    async def get_by_external_id(self, provider: str, external_id: str) -> User | None:
        """Async function missing docstring."""
        query = (
            "SELECT * FROM benefitiq.users FINAL "
            "WHERE authentication_provider = %(provider)s "
            "AND external_provider_id = %(external_id)s"
        )
        result = await self.db.query_async(
            query,
            {"provider": provider, "external_id": external_id}
        )
        if not result.result_rows:
            return None
        return self._map_row_to_user(result.result_rows[0])

    async def update(self, user: User) -> User:
        # ReplacingMergeTree handles updates by inserting a newer row
        """Async function missing docstring."""
        return await self.create(user)

    async def list(self, offset: int, limit: int) -> list[User]:
        """Lists users with pagination."""
        query = (
            "SELECT * FROM benefitiq.users FINAL "
            "ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s"
        )
        result = await self.db.query_async(query, {"limit": limit, "offset": offset})
        return [self._map_row_to_user(row) for row in result.result_rows]

    async def delete(self, user_id: UUID) -> bool:
        """Deactivates/soft deletes user in ClickHouse ReplacingMergeTree datastore."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await self.update(user)
        return True

    async def query_generic(self, request: QueryRequest) -> QueryResponse:
        """Executes datatype-aware generic query with filters, sorting, and pagination."""
        from benefit_iq.api.schemas.query import QueryResponse
        from benefit_iq.infrastructure.persistence.clickhouse.query_builder import ClickHouseQueryBuilder

        builder = ClickHouseQueryBuilder(
            table_name="benefitiq.users FINAL",
            allowed_fields={
                "id": "id",
                "username": "username",
                "first_name": "first_name",
                "middle_name": "middle_name",
                "last_name": "last_name",
                "email": "email",
                "role_id": "role_id",
                "is_active": "is_active",
                "is_email_verified": "is_email_verified",
                "created_at": "created_at",
                "updated_at": "updated_at",
                "last_login_at": "last_login_at",
            },
        )
        data_sql, count_sql, params, limit, offset = builder.build_query(request)

        count_res = await self.db.query_async(count_sql, params)
        total = count_res.result_rows[0][0] if (count_res and count_res.result_rows) else 0

        data_res = await self.db.query_async(data_sql, params)
        items = []
        if data_res and data_res.result_rows:
            for row in data_res.result_rows:
                u = self._map_row_to_user(row)
                items.append({
                    "id": str(u.id),
                    "username": u.username,
                    "first_name": u.first_name,
                    "middle_name": u.middle_name,
                    "last_name": u.last_name,
                    "email": u.email,
                    "role_id": str(u.role_id),
                    "is_active": u.is_active,
                    "is_email_verified": u.is_email_verified,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                })

        total_pages = (total + request.page_size - 1) // request.page_size if request.page_size else 1
        return QueryResponse(
            items=items,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )
