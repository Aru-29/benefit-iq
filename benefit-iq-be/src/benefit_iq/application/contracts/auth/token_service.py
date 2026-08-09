"""
Module missing docstring.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class TokenPayload:
    """Class missing docstring."""
    user_id: UUID
    role_id: UUID
    session_id: str
    token_type: str
    exp: datetime
    jti: str


@dataclass
class TokenPair:
    """Class missing docstring."""
    access_token: str
    refresh_token: str
    expires_in: int


class TokenService(ABC):
    """Class missing docstring."""

    @abstractmethod
    def generate_token_pair(self, user_id: UUID, role_id: UUID, session_id: str) -> TokenPair:
        """Function missing docstring."""
        ...

    @abstractmethod
    def decode_token(self, token: str) -> TokenPayload:
        """Function missing docstring."""
        ...

    @abstractmethod
    def generate_verification_token(self, user_id: UUID) -> str:
        """Function missing docstring."""
        ...

    @abstractmethod
    def decode_verification_token(self, token: str) -> UUID:
        """Function missing docstring."""
        ...

    @abstractmethod
    def generate_password_reset_token(self, user_id: UUID) -> str:
        """Function missing docstring."""
        ...

    @abstractmethod
    def decode_password_reset_token(self, token: str) -> UUID:
        """Function missing docstring."""
        ...
