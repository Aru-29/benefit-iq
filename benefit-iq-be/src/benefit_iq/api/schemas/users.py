"""
Module missing docstring.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    """Class missing docstring."""
    id: UUID
    username: str
    first_name: str
    middle_name: str | None
    last_name: str
    email: str
    role_id: UUID
    role_name: str | None = "CUSTOMER"
    is_active: bool
    is_email_verified: bool
    preferred_settings: dict | None
    created_at: datetime
    last_login_at: datetime | None


class UpdateProfileRequest(BaseModel):
    """Class missing docstring."""
    first_name: str
    last_name: str
    username: str
    middle_name: str | None = None
    preferred_settings: dict | None = None
