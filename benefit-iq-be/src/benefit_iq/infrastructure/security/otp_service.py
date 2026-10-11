"""Secure 2-Step OTP Generation, Hashing, Expiration, and Attempt Limit Service."""

import hashlib
import json
import secrets
from typing import Any

import structlog
from opentelemetry import trace
from redis.asyncio import Redis

from benefit_iq.infrastructure.utils.retry import with_retry

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


class OtpService:
    """Service managing 2-Step OTP creation, hashed Redis storage, attempt limits, and single-use verification."""

    def __init__(self, redis_client: Redis) -> None:
        """Initialize OtpService with Redis client."""
        self.redis = redis_client

    def _hash_otp(self, otp: str) -> str:
        """Computes SHA-256 hash of OTP for secure storage."""
        return hashlib.sha256(otp.encode("utf-8")).hexdigest()

    def _otp_key(self, purpose: str, key: str) -> str:
        return f"otp:{purpose}:{str(key).strip().lower()}"

    def _attempts_key(self, purpose: str, key: str) -> str:
        return f"otp_attempts:{purpose}:{str(key).strip().lower()}"

    def _pending_reg_key(self, email: str) -> str:
        return f"pending_reg:{str(email).strip().lower()}"

    async def generate_otp(self, purpose: str, key: str, ttl_seconds: int = 600) -> str:
        """Generates a secure 6-digit OTP, stores its SHA-256 hash in Redis, and resets attempt counter."""
        with tracer.start_as_current_span("generate_otp") as span:
            span.set_attribute("otp.purpose", purpose)

            otp = f"{secrets.randbelow(900000) + 100000:06d}"
            otp_hash = self._hash_otp(otp)

            async def do_store() -> None:
                await self.redis.setex(self._otp_key(purpose, key), ttl_seconds, otp_hash)
                await self.redis.setex(self._attempts_key(purpose, key), ttl_seconds, "0")

            await with_retry(do_store, operation_name="redis_store_otp")
            logger.info("otp_generated", purpose=purpose, key=key)
            return otp

    async def verify_otp(
        self, purpose: str, key: str, submitted_otp: str, max_attempts: int = 3
    ) -> bool:
        """Verifies submitted OTP against stored hash, enforcing expiration, attempt limits, and single-use semantics."""
        # One Redis operation enforces attempt limits and single-use under concurrency.
        script = """
        local expected = redis.call('GET', KEYS[1])
        if not expected then return 0 end
        local attempts = tonumber(redis.call('GET', KEYS[2]) or '0')
        if attempts >= tonumber(ARGV[2]) then
            redis.call('DEL', KEYS[1], KEYS[2]); return 0
        end
        if expected == ARGV[1] then
            redis.call('DEL', KEYS[1], KEYS[2]); return 1
        end
        redis.call('INCR', KEYS[2])
        redis.call('EXPIRE', KEYS[2], 600)
        return 0
        """
        result = await self.redis.eval(
            script,
            2,
            self._otp_key(purpose, key),
            self._attempts_key(purpose, key),
            self._hash_otp(str(submitted_otp).strip()),
            max_attempts,
        )
        return bool(result)

    async def store_pending_registration(
        self, email: str, data: dict[str, Any], ttl_seconds: int = 600
    ) -> None:
        """Stores pending registration data JSON in Redis prior to OTP verification."""
        key = self._pending_reg_key(email)
        payload = json.dumps(data)

        async def do_store() -> None:
            await self.redis.setex(key, ttl_seconds, payload)

        await with_retry(do_store, operation_name="redis_store_pending_reg")

    async def get_pending_registration(self, email: str) -> dict[str, Any] | None:
        """Retrieves pending registration payload prior to account creation."""
        key = self._pending_reg_key(email)
        raw = await self.redis.get(key)
        if not raw:
            return None
        payload_str = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        return json.loads(payload_str)

    async def delete_pending_registration(self, email: str) -> None:
        """Deletes pending registration payload after successful account creation."""
        key = self._pending_reg_key(email)
        await self.redis.delete(key)
