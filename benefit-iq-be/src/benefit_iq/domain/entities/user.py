"""
Module missing docstring.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from benefit_iq.domain.enums.auth_provider import AuthProvider


@dataclass
class User:
    """Class missing docstring."""
    id: UUID
    username: str
    first_name: str
    middle_name: str | None
    last_name: str
    email: str
    password_hash: str | None
    role_id: UUID
    authentication_provider: AuthProvider
    external_provider_id: str | None
    is_active: bool
    is_email_verified: bool
    preferred_settings: dict | None
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    def activate(self) -> None:
        """Function missing docstring."""
        self.is_active = True

    def deactivate(self) -> None:
        """Function missing docstring."""
        self.is_active = False

    def verify_email(self) -> None:
        """Function missing docstring."""
        self.is_email_verified = True

    def update_last_login(self, login_time: datetime) -> None:
        """Function missing docstring."""
        self.last_login_at = login_time
