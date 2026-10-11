"""
Module missing docstring.
"""

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Class missing docstring."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Function missing docstring."""
        ...

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Function missing docstring."""
        ...
