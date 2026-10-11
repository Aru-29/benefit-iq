"""AppConfig API Request and Response Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateConfigRequest(BaseModel):
    """Request payload for creating or setting an app configuration key."""

    config_key: str = Field(..., description="Configuration property key (e.g. JWT_SECRET_KEY)")
    value: str = Field(..., description="Configuration value string")
    is_secret: bool = Field(
        False, description="Flag indicating if the value is a secret stored in OpenBao"
    )
    secret_path: str | None = Field(
        None, description="OpenBao Vault secret path if is_secret is true"
    )
    secret_key: str | None = Field(
        None, description="OpenBao Vault secret key inside path if is_secret is true"
    )
    description: str | None = Field(
        None, description="Human-readable description of configuration property"
    )
    application: str | None = Field("benefit-iq-be", description="Target application name")
    environment: str | None = Field("development", description="Target environment name")


class UpdateConfigRequest(BaseModel):
    """Request payload for updating an existing app configuration key."""

    value: str = Field(..., description="New configuration value string")
    is_secret: bool = Field(
        False, description="Flag indicating if the value is a secret stored in OpenBao"
    )
    secret_path: str | None = Field(
        None, description="OpenBao Vault secret path if is_secret is true"
    )
    secret_key: str | None = Field(
        None, description="OpenBao Vault secret key inside path if is_secret is true"
    )
    description: str | None = Field(
        None, description="Human-readable description of configuration property"
    )


class AppConfigResponse(BaseModel):
    """Response payload representing an app configuration entry."""

    id: UUID
    application: str
    environment: str
    config_key: str
    config_value: str | None
    is_secret: bool
    secret_path: str | None
    secret_key: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
