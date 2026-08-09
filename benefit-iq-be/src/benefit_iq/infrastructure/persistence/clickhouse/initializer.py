"""ClickHouse schema initialization and runtime verification.

Verifies table existence and essential system records on startup while
delegating full schema creation to external DDL scripts (scripts/init_clickhouse.sql).
"""
from uuid import uuid4
import structlog
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase

logger = structlog.get_logger(__name__)


class ClickHouseInitializer:
    """Verifies ClickHouse core tables and lightweight runtime readiness."""

    def __init__(self, database: ClickHouseDatabase) -> None:
        """Initialize initializer dependencies."""
        self.db = database

    async def initialize(self) -> None:
        """Verifies core ClickHouse database tables and minimal system roles."""
        logger.info("clickhouse_initialization_started")

        # 1. Create tables if not existing
        await self.db.execute_async("""
        CREATE TABLE IF NOT EXISTS benefitiq.roles (
            id UUID,
            name String,
            description Nullable(String),
            is_active UInt8,
            created_at DateTime,
            updated_at DateTime
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (name, id);
        """)

        await self.db.execute_async("""
        CREATE TABLE IF NOT EXISTS benefitiq.users (
            id UUID,
            username String,
            first_name String,
            last_name String,
            email String,
            password_hash String,
            role_id UUID,
            is_active UInt8,
            is_email_verified UInt8,
            created_at DateTime,
            updated_at DateTime,
            last_login_at Nullable(DateTime)
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (email, id);
        """)

        await self.db.execute_async("""
        CREATE TABLE IF NOT EXISTS benefitiq.app_config (
            id UUID,
            application String,
            environment String,
            config_key String,
            config_value Nullable(String),
            is_secret UInt8,
            secret_path Nullable(String),
            secret_key Nullable(String),
            description Nullable(String),
            is_active UInt8,
            created_at DateTime,
            updated_at DateTime
        ) ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (application, environment, config_key, id);
        """)

        # 2. Idempotent seed for basic roles if missing
        await self._ensure_roles()
        logger.info("clickhouse_initialization_completed")

    async def _ensure_roles(self) -> None:
        """Idempotently ensures essential roles (ADMIN, CUSTOMER) exist in ClickHouse."""
        roles = [
            ("ADMIN", "System Administrator Role"),
            ("CUSTOMER", "Standard Customer Role"),
        ]
        for role_name, description in roles:
            result = await self.db.query_async(
                "SELECT id FROM benefitiq.roles FINAL WHERE name = %(name)s",
                {"name": role_name},
            )
            if not result.result_rows:
                role_id = str(uuid4())
                role_sql = (
                    "INSERT INTO benefitiq.roles "
                    "(id, name, description, is_active, created_at, updated_at) "
                    "VALUES (%s, %s, %s, 1, now(), now())"
                )
                await self.db.execute_async(role_sql, [role_id, role_name, description])
                logger.info("seeded_essential_role", role_name=role_name)
