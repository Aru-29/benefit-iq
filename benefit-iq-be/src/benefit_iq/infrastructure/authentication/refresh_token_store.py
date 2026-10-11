"""
Module missing docstring.
"""

from redis.asyncio import Redis

from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.infrastructure.utils.retry import with_retry


class RedisRefreshTokenStore(RefreshTokenStore):
    """Class missing docstring."""

    def __init__(self, redis_client: Redis) -> None:
        """Function missing docstring."""
        self.redis = redis_client

    def _session_key(self, session_id: str) -> str:
        """Function missing docstring."""
        return f"session:{session_id}"

    def _jti_key(self, jti: str) -> str:
        """Function missing docstring."""
        return f"rt:{jti}"

    async def store_token(self, jti: str, user_id: str, session_id: str, expires_in: int) -> None:
        """Async function missing docstring."""

        async def do_store() -> None:
            # We track the session to easily revoke all tokens for a session
            """Async function missing docstring."""
            await self.redis.sadd(self._session_key(session_id), jti)
            await self.redis.expire(self._session_key(session_id), expires_in)

            # We track the individual token to detect reuse
            await self.redis.setex(self._jti_key(jti), expires_in, "valid")

        await with_retry(do_store, operation_name="redis_store_token")

    async def is_valid(self, jti: str) -> bool:
        """Async function missing docstring."""

        async def do_check() -> bool:
            """Async function missing docstring."""
            return await self.redis.exists(self._jti_key(jti)) == 1

        return await with_retry(do_check, operation_name="redis_is_valid_token")

    async def revoke_token(self, jti: str) -> None:
        """Async function missing docstring."""

        async def do_revoke() -> None:
            """Async function missing docstring."""
            await self.redis.delete(self._jti_key(jti))

        await with_retry(do_revoke, operation_name="redis_revoke_token")

    async def revoke_session(self, session_id: str) -> None:
        """Async function missing docstring."""

        async def do_revoke_session() -> None:
            """Async function missing docstring."""
            session_key = self._session_key(session_id)
            jtis = await self.redis.smembers(session_key)
            if jtis:
                # Delete all tokens in the session
                keys_to_delete = [
                    self._jti_key(jti.decode("utf-8") if isinstance(jti, bytes) else jti)
                    for jti in jtis
                ]
                await self.redis.delete(*keys_to_delete)
            # Delete the session itself
            await self.redis.delete(session_key)

        await with_retry(do_revoke_session, operation_name="redis_revoke_session")

    async def is_session_valid(self, session_id: str) -> bool:
        """Async function missing docstring."""

        async def do_check() -> bool:
            """Async function missing docstring."""
            return await self.redis.exists(self._session_key(session_id)) == 1

        return await with_retry(do_check, operation_name="redis_is_valid_session")

    async def consume_token(self, jti: str) -> bool:
        return await self.redis.getdel(self._jti_key(jti)) is not None
