"""Generic Lookup API Schemas.

Defines standardized lookup request and response structures for dropdowns,
autocompletes, and infinite-scroll lookups across backend entities.
"""

from typing import Any

from pydantic import BaseModel, Field


class GenericLookupRequest(BaseModel):
    """Unified request model for entity lookup endpoints."""

    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    is_active_only: bool = True
    cursor: str | None = None


class LookupItem(BaseModel):
    """Standardized key-value item for UI dropdowns/autocompletes."""

    id: str
    label: str
    value: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenericLookupResponse(BaseModel):
    """Unified response model for entity lookup endpoints."""

    items: list[LookupItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    next_cursor: str | None = None
