"""Hybrid Database & Redis Refresh Token Store for Benefit IQ.

Persists user sessions and refresh token JTIs in ClickHouse datastore (benefitiq.user_sessions)
while leveraging Redis for fast read-through caching and immediate session revocation.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from redis.asyncio import Redis

from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.infrastructure.persistence.clickhouse.database import ClickHouseDatabase
from benefit_iq.infrastructure.utils.retry import with_retry

logger = structlog.get_logger(__name__)


class HybridRefreshTokenStore(RefreshTokenStore):
    """Hybrid Refresh Token Store combining primary ClickHouse datastore with Redis cache."""

    def __init__(self, clickhouse_db: ClickHouseDatabase, redis_client: Redis) -> None:
        """Initialize hybrid refresh token store with database and Redis client."""
        self.db = clickhouse_db
        self.redis = redis_client

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def _jti_key(self, jti: str) -> str:
        return f"rt:{jti}"

    async def store_token(self, jti: str, user_id: str, session_id: str, expires_in: int) -> None:
        """Stores refresh token record in ClickHouse and populates Redis cache."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=expires_in)

        # 1. Write to primary ClickHouse datastore
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.client.insert(
                "user_sessions",
                [
                    [
                        UUID(session_id),
                        UUID(user_id),
                        jti,
                        0,  # is_revoked = 0
                        expires_at,
                        now,
                        now,
                    ]
                ],
                column_names=[
                    "id",
                    "user_id",
                    "jti",
                    "is_revoked",
                    "expires_at",
                    "created_at",
                    "updated_at",
                ],
            ),
        )

        # 2. Populate Redis cache
        async def do_cache_store() -> None:
            await self.redis.sadd(self._session_key(session_id), jti)
            await self.redis.expire(self._session_key(session_id), expires_in)
            await self.redis.setex(self._jti_key(jti), expires_in, "valid")

        await with_retry(do_cache_store, operation_name="redis_cache_store_token")

    async def is_valid(self, jti: str) -> bool:
        """Checks token validity in Redis cache first, falling back to ClickHouse on cache miss."""

        # 1. Check Redis cache
        async def do_cache_check() -> bool | None:
            val = await self.redis.get(self._jti_key(jti))
            if val is not None:
                return val.decode("utf-8") == "valid" if isinstance(val, bytes) else val == "valid"
            return None

        cached_status = await with_retry(do_cache_check, operation_name="redis_cache_is_valid")
        if cached_status is not None:
            return cached_status

        # 2. Cache miss -> Fallback to ClickHouse
        result = await self.db.query_async(
            "SELECT is_revoked, expires_at FROM benefitiq.user_sessions FINAL WHERE jti = %(jti)s",
            {"jti": jti},
        )
        if not result.result_rows:
            return False

        is_revoked, expires_at = result.result_rows[0]
        now = datetime.now(UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        valid = (is_revoked == 0) and (expires_at > now)

        # Re-populate cache if valid
        if valid:
            ttl = int((expires_at - now).total_seconds())
            if ttl > 0:
                await self.redis.setex(self._jti_key(jti), ttl, "valid")

        return valid

    async def revoke_token(self, jti: str) -> None:
        """Revokes a specific token JTI in ClickHouse datastore and invalidates Redis cache."""
        now = datetime.now(UTC)

        # Find existing session record
        result = await self.db.query_async(
            "SELECT id, user_id, expires_at, created_at FROM benefitiq.user_sessions FINAL WHERE jti = %(jti)s",
            {"jti": jti},
        )
        if result.result_rows:
            session_id, user_id, expires_at, created_at = result.result_rows[0]
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.client.insert(
                    "user_sessions",
                    [[session_id, user_id, jti, 1, expires_at, created_at, now]],
                    column_names=[
                        "id",
                        "user_id",
                        "jti",
                        "is_revoked",
                        "expires_at",
                        "created_at",
                        "updated_at",
                    ],
                ),
            )

        # Invalidate Redis cache
        async def do_cache_revoke() -> None:
            await self.redis.delete(self._jti_key(jti))

        await with_retry(do_cache_revoke, operation_name="redis_cache_revoke_token")

    async def revoke_session(self, session_id: str) -> None:
        """Revokes all tokens associated with a session in ClickHouse and Redis."""
        now = datetime.now(UTC)

        # 1. Update ClickHouse
        result = await self.db.query_async(
            "SELECT user_id, jti, expires_at, created_at FROM benefitiq.user_sessions FINAL WHERE id = %(session_id)s",
            {"session_id": session_id},
        )
        if result.result_rows:
            rows_to_insert = [
                [UUID(session_id), user_id, jti, 1, expires_at, created_at, now]
                for user_id, jti, expires_at, created_at in result.result_rows
            ]
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.client.insert(
                    "user_sessions",
                    rows_to_insert,
                    column_names=[
                        "id",
                        "user_id",
                        "jti",
                        "is_revoked",
                        "expires_at",
                        "created_at",
                        "updated_at",
                    ],
                ),
            )

        # 2. Update Redis
        async def do_cache_revoke_session() -> None:
            session_key = self._session_key(session_id)
            jtis = await self.redis.smembers(session_key)
            if jtis:
                keys_to_delete = [
                    self._jti_key(jti.decode("utf-8") if isinstance(jti, bytes) else jti)
                    for jti in jtis
                ]
                if keys_to_delete:
                    await self.redis.delete(*keys_to_delete)
            await self.redis.delete(session_key)

        await with_retry(do_cache_revoke_session, operation_name="redis_cache_revoke_session")

    async def is_session_valid(self, session_id: str) -> bool:
        """Checks whether a session is valid in Redis cache or ClickHouse datastore."""

        async def do_cache_session_check() -> bool:
            return await self.redis.exists(self._session_key(session_id)) == 1

        if await with_retry(do_cache_session_check, operation_name="redis_cache_is_session_valid"):
            return True

        result = await self.db.query_async(
            "SELECT is_revoked, expires_at FROM benefitiq.user_sessions FINAL WHERE id = %(session_id)s",
            {"session_id": session_id},
        )
        if not result.result_rows:
            return False

        now = datetime.now(UTC)
        return any(
            is_revoked == 0
            and (expires_at.replace(tzinfo=UTC) if expires_at.tzinfo is None else expires_at) > now
            for is_revoked, expires_at in result.result_rows
        )
