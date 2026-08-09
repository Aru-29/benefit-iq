"""
Module missing docstring.
"""
from pydantic import BaseModel, Field


class PaginationRequest(BaseModel):
    """Class missing docstring."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    @property
    def offset(self) -> int:
        """Function missing docstring."""
        return (self.page - 1) * self.page_size
