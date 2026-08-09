"""
Module missing docstring.
"""
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickHouseSettings(BaseSettings):
    """Class missing docstring."""
    host: str = "localhost"
    port: int = 8123
    username: str = "default"
    password: str = ""
    database: str = "benefitiq"
    secure: bool = False
    connect_timeout: int = 10
    send_receive_timeout: int = 30

    model_config = SettingsConfigDict(
        env_prefix="CLICKHOUSE_",
        extra="ignore",
    )


class RedisSettings(BaseSettings):
    """Class missing docstring."""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    database: int = 0
    enabled: bool = True

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore",
    )


class TelemetrySettings(BaseSettings):
    """Class missing docstring."""
    enabled: bool = True
    service_name: str = "benefitiq-api"
    exporter_otlp_endpoint: str = "http://localhost:4317"

    model_config = SettingsConfigDict(
        env_prefix="OTEL_",
        extra="ignore",
    )


class JWTSettings(BaseSettings):
    """Class missing docstring."""
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        extra="ignore",
    )


class OAuthSettings(BaseSettings):
    """Class missing docstring."""
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    redirect_base_url: str = "http://localhost:8080"

    model_config = SettingsConfigDict(
        env_prefix="OAUTH_",
        extra="ignore",
    )


class EmailSettings(BaseSettings):
    """Class missing docstring."""
    enabled: bool = True
    host: str = "localhost"
    port: int = 1025
    username: str = ""
    password: str = ""
    from_address: str = "noreply@benefitiq.com"
    use_tls: bool = False

    model_config = SettingsConfigDict(
        env_prefix="SMTP_",
        extra="ignore",
    )


class SecuritySettings(BaseSettings):
    """Class missing docstring."""
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    encryption_private_key_path: str = ""

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        extra="ignore",
    )


class InitializationSettings(BaseSettings):
    """Class missing docstring."""
    admin_email: str = "admin@benefitiq.com"
    admin_password: str = "Admin@123!"

    model_config = SettingsConfigDict(
        env_prefix="INIT_",
        extra="ignore",
    )


class Settings(BaseSettings):

    """Class missing docstring."""
    app_name: str = "BenefitIQ"
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = False

    api_prefix: str = "/api"
    api_version: str = "v1"

    log_level: str = "INFO"
    log_json: bool = False

    cors_origins: list[str] | str = Field(
        default_factory=lambda: [
            "http://localhost:4200",
        ]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Function missing docstring."""
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    clickhouse: ClickHouseSettings = Field(
        default_factory=ClickHouseSettings
    )

    redis: RedisSettings = Field(
        default_factory=RedisSettings
    )

    telemetry: TelemetrySettings = Field(
        default_factory=TelemetrySettings
    )

    jwt: JWTSettings = Field(
        default_factory=JWTSettings
    )

    oauth: OAuthSettings = Field(
        default_factory=OAuthSettings
    )

    email: EmailSettings = Field(
        default_factory=EmailSettings
    )

    security: SecuritySettings = Field(
        default_factory=SecuritySettings
    )

    init: InitializationSettings = Field(
        default_factory=InitializationSettings
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Function missing docstring."""
    return Settings()
