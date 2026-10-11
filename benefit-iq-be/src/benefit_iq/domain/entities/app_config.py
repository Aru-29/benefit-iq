"""AppConfig Domain Entity."""

# pylint: disable=too-many-instance-attributes,line-too-long
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AppConfig:
    """Represents a dynamic configuration setting entry stored in database / cache / secret manager."""

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
