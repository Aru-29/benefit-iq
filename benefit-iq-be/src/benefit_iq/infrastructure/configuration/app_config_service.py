"""Dynamic Application Configuration Service with Redis Read-Through Caching and OpenBao Vault Integration."""
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,line-too-long
from datetime import datetime, timezone
from uuid import uuid4

import structlog
from redis.asyncio import Redis

from benefit_iq.application.contracts.auth.secret_manager import SecretManager
from benefit_iq.application.contracts.repositories.app_config_repository import AppConfigRepository
from benefit_iq.domain.entities.app_config import AppConfig
from benefit_iq.infrastructure.utils.retry import with_retry

logger = structlog.get_logger(__name__)


class AppConfigService:
    """Hybrid Configuration Service integrating ClickHouse, Redis Cache, and OpenBao Secret Storage."""

    def __init__(
        self,
        repository: AppConfigRepository,
        redis_client: Redis,
        secret_manager: SecretManager | None = None,
        default_app: str = "benefit-iq-be",
        default_env: str = "development",
    ) -> None:
        """Initialize configuration service dependencies."""
        self.repository = repository
        self.redis = redis_client
        self.secret_manager = secret_manager
        self.default_app = default_app
        self.default_env = default_env

    def _cache_key(self, config_key: str, app: str, env: str) -> str:
        """Generates Redis cache key for a configuration entry."""
        return f"app_config:{app}:{env}:{config_key}"

    async def get_config(
        self, config_key: str, app: str | None = None, env: str | None = None
    ) -> str | None:
        """Retrieves a configuration value from Redis cache -> ClickHouse -> OpenBao."""
        application = app or self.default_app
        environment = env or self.default_env
        cache_key = self._cache_key(config_key, application, environment)

        # 1. Check Redis cache
        async def do_cache_get() -> str | None:
            val = await self.redis.get(cache_key)
            if val is not None:
                return val.decode("utf-8") if isinstance(val, bytes) else str(val)
            return None

        cached_val = await with_retry(do_cache_get, operation_name="redis_get_config")
        if cached_val is not None:
            return cached_val

        # 2. Cache miss -> Query ClickHouse
        cfg = await self.repository.get_by_key(application, environment, config_key)
        if not cfg:
            return None

        final_value = cfg.config_value

        # 3. If secret -> Fetch from OpenBao Vault
        if cfg.is_secret and cfg.secret_path and cfg.secret_key and self.secret_manager:
            try:
                secret_val = await self.secret_manager.get_secret(
                    cfg.secret_path, cfg.secret_key
                )
                if secret_val:
                    final_value = secret_val
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "openbao_secret_fetch_failed_using_db_fallback",
                    path=cfg.secret_path,
                    key=cfg.secret_key,
                    error=str(e),
                )

        # 4. Cache resolved valid value in Redis (TTL 3600 seconds)
        if final_value and str(final_value).strip():
            async def do_cache_set() -> None:
                await self.redis.setex(cache_key, 3600, final_value)

            await with_retry(do_cache_set, operation_name="redis_set_config")

        return final_value

    async def set_config(
        self,
        config_key: str,
        value: str,
        is_secret: bool = False,
        secret_path: str | None = None,
        secret_key: str | None = None,
        description: str | None = None,
        app: str | None = None,
        env: str | None = None,
    ) -> AppConfig:
        """Creates or updates a configuration key, persisting secrets to OpenBao and caching in Redis."""
        application = app or self.default_app
        environment = env or self.default_env
        now = datetime.now(timezone.utc)

        target_secret_path = secret_path
        target_secret_key = secret_key

        if is_secret:
            if not target_secret_path:
                target_secret_path = f"secret/data/{application}/{config_key.lower()}"
            if not target_secret_key:
                target_secret_key = "secret_value"

            # Persist secret to OpenBao
            if self.secret_manager:
                try:
                    await self.secret_manager.set_secret(
                        target_secret_path, {target_secret_key: value}
                    )
                    logger.info(
                        "openbao_secret_stored",
                        key=config_key,
                        path=target_secret_path,
                    )
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.error(
                        "openbao_secret_storage_failed",
                        key=config_key,
                        error=str(e),
                    )

            # Store value in ClickHouse as fallback
            db_config_value = value
        else:
            db_config_value = value

        existing = await self.repository.get_by_key(application, environment, config_key)
        if existing:
            config_entity = AppConfig(
                id=existing.id,
                application=application,
                environment=environment,
                config_key=config_key,
                config_value=db_config_value,
                is_secret=is_secret,
                secret_path=target_secret_path,
                secret_key=target_secret_key,
                description=description or existing.description,
                is_active=True,
                created_at=existing.created_at,
                updated_at=now,
            )
            saved = await self.repository.update(config_entity)
        else:
            config_entity = AppConfig(
                id=uuid4(),
                application=application,
                environment=environment,
                config_key=config_key,
                config_value=db_config_value,
                is_secret=is_secret,
                secret_path=target_secret_path,
                secret_key=target_secret_key,
                description=description,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            saved = await self.repository.create(config_entity)

        # Update Redis cache immediately
        cache_key = self._cache_key(config_key, application, environment)

        async def do_cache_update() -> None:
            await self.redis.setex(cache_key, 3600, value)

        await with_retry(do_cache_update, operation_name="redis_update_config")
        return saved

    async def list_configs(
        self, app: str | None = None, env: str | None = None
    ) -> list[AppConfig]:
        """Lists active configuration entries."""
        application = app or self.default_app
        environment = env or self.default_env
        return await self.repository.list_configs(application, environment)

    async def delete_config(
        self, config_key: str, app: str | None = None, env: str | None = None
    ) -> bool:
        """Deletes configuration key and invalidates Redis cache."""
        application = app or self.default_app
        environment = env or self.default_env

        success = await self.repository.delete(application, environment, config_key)
        if success:
            cache_key = self._cache_key(config_key, application, environment)

            async def do_cache_delete() -> None:
                await self.redis.delete(cache_key)

            await with_retry(do_cache_delete, operation_name="redis_delete_config")

        return success
