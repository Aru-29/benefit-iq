"""
Module missing docstring.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Role:
    """Class missing docstring."""

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def update(
        self,
        name: str,
        description: str | None,
    ) -> None:
        """Function missing docstring."""
        self.name = name
        self.description = description

    def deactivate(self) -> None:
        """Function missing docstring."""
        self.is_active = False

    def activate(self) -> None:
        """Function missing docstring."""
        self.is_active = True
