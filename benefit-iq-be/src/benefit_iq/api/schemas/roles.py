"""
Module missing docstring.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleResponse(BaseModel):
    """Class missing docstring."""
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CreateRoleRequest(BaseModel):
    """Class missing docstring."""
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class UpdateRoleRequest(BaseModel):
    """Class missing docstring."""
    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    is_active: bool
