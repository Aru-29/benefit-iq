"""
Module missing docstring.
"""
from dataclasses import dataclass

from benefit_iq.domain.exceptions.role_exceptions import (
    InvalidRoleNameException,
)


@dataclass(frozen=True)
class RoleName:
    """Class missing docstring."""
    value: str

    def __post_init__(self) -> None:
        """Function missing docstring."""
        value = self.value.strip()

        if not value:
            raise InvalidRoleNameException(
                "Role name cannot be empty."
            )

        if len(value) > 100:
            raise InvalidRoleNameException(
                "Role name cannot exceed 100 characters."
            )

        object.__setattr__(self, "value", value)
