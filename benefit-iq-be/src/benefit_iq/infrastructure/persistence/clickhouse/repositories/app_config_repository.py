"""ClickHouse implementation of AppConfigRepository."""
import asyncio
from datetime import datetime, timezone

from benefit_iq.application.contracts.repositories.app_config_repository import AppConfigRepository
from benefit_iq.domain.entities.app_config import AppConfig
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase


class ClickHouseAppConfigRepository(AppConfigRepository):
    """ClickHouse implementation of the AppConfigRepository interface."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        """Initialize repository with ClickHouse database connection."""
        self.db = database

    def _map_row_to_config(self, row: tuple) -> AppConfig:
        """Maps a database row tuple to an AppConfig domain entity."""
        return AppConfig(
            id=row[0],
            application=row[1],
            environment=row[2],
            config_key=row[3],
            config_value=row[4] if row[4] else None,
            is_secret=bool(row[5]),
            secret_path=row[6] if row[6] else None,
            secret_key=row[7] if row[7] else None,
            description=row[8] if row[8] else None,
            is_active=bool(row[9]),
            created_at=row[10],
            updated_at=row[11],
        )

    async def create(self, config: AppConfig) -> AppConfig:
        """Inserts an app configuration record into ClickHouse datastore."""
        data = [[
            str(config.id),
            config.application,
            config.environment,
            config.config_key,
            config.config_value if config.config_value is not None else "",
            1 if config.is_secret else 0,
            config.secret_path or "",
            config.secret_key or "",
            config.description or "",
            1 if config.is_active else 0,
            config.created_at,
            config.updated_at,
        ]]
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "app_config",
                data,
                column_names=[
                    "id",
                    "application",
                    "environment",
                    "config_key",
                    "config_value",
                    "is_secret",
                    "secret_path",
                    "secret_key",
                    "description",
                    "is_active",
                    "created_at",
                    "updated_at",
                ],
            ),
        )
        return config

    async def get_by_key(
        self, application: str, environment: str, config_key: str
    ) -> AppConfig | None:
        """Fetches active configuration entry by application, environment, and config key."""
        query = (
            "SELECT id, application, environment, config_key, config_value, is_secret, "
            "secret_path, secret_key, description, is_active, created_at, updated_at "
            "FROM benefitiq.app_config FINAL "
            "WHERE application = %(app)s AND environment = %(env)s "
            "AND config_key = %(key)s AND is_active = 1"
        )
        result = await self.db.query_async(
            query, {"app": application, "env": environment, "key": config_key}
        )
        if not result.result_rows:
            return None
        return self._map_row_to_config(result.result_rows[0])

    async def list_configs(
        self, application: str, environment: str
    ) -> list[AppConfig]:
        """Lists all active configuration entries for an application and environment."""
        query = (
            "SELECT id, application, environment, config_key, config_value, is_secret, "
            "secret_path, secret_key, description, is_active, created_at, updated_at "
            "FROM benefitiq.app_config FINAL "
            "WHERE application = %(app)s AND environment = %(env)s AND is_active = 1 "
            "ORDER BY config_key ASC"
        )
        result = await self.db.query_async(
            query, {"app": application, "env": environment}
        )
        return [self._map_row_to_config(row) for row in result.result_rows]

    async def update(self, config: AppConfig) -> AppConfig:
        """Updates an existing configuration record using ReplacingMergeTree versioning."""
        return await self.create(config)

    async def delete(
        self, application: str, environment: str, config_key: str
    ) -> bool:
        """Deactivates/soft deletes configuration entry by setting is_active = 0."""
        cfg = await self.get_by_key(application, environment, config_key)
        if not cfg:
            return False
        cfg.is_active = False
        cfg.updated_at = datetime.now(timezone.utc)
        await self.update(cfg)
        return True

    async def query_generic(self, request) -> Any:
        """Executes generic query across app_config table."""
        from benefit_iq.api.schemas.query import QueryResponse
        from benefit_iq.infrastructure.persistence.clickhouse.query_builder import ClickHouseQueryBuilder

        builder = ClickHouseQueryBuilder(
            table_name="benefitiq.app_config FINAL",
            allowed_fields={
                "id": "id",
                "application": "application",
                "environment": "environment",
                "config_key": "config_key",
                "config_value": "config_value",
                "is_secret": "is_secret",
                "secret_path": "secret_path",
                "secret_key": "secret_key",
                "description": "description",
                "is_active": "is_active",
                "created_at": "created_at",
                "updated_at": "updated_at",
            },
        )
        data_sql, count_sql, params, limit, offset = builder.build_query(request)

        count_res = await self.db.query_async(count_sql, params)
        total = count_res.result_rows[0][0] if (count_res and count_res.result_rows) else 0

        data_res = await self.db.query_async(data_sql, params)
        items = []
        if data_res and data_res.result_rows:
            for row in data_res.result_rows:
                c = self._map_row_to_config(row)
                items.append({
                    "id": str(c.id),
                    "application": c.application,
                    "environment": c.environment,
                    "config_key": c.config_key,
                    "config_value": c.config_value if not c.is_secret else "*****",
                    "is_secret": c.is_secret,
                    "secret_path": c.secret_path,
                    "secret_key": c.secret_key,
                    "description": c.description,
                    "is_active": c.is_active,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                })

        total_pages = (total + request.page_size - 1) // request.page_size if request.page_size else 1
        return QueryResponse(
            items=items,
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )
