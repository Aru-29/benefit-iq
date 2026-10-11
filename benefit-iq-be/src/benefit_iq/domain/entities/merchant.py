"""Merchant domain entity.

Represents a merchant where transactions can occur.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Merchant:
    """A merchant entity with category and location information."""

    id: UUID
    name: str
    merchant_category_code: str
    category_name: str
    country: str | None
    city: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
