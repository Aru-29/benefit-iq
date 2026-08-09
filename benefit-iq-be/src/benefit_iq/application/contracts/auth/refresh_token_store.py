"""
Module missing docstring.
"""
from abc import ABC, abstractmethod
from typing import Optional


class RefreshTokenStore(ABC):
    """Contract for managing refresh token families and session tracking."""

    @abstractmethod
    async def store_token(self, jti: str, user_id: str, session_id: str, expires_in: int) -> None:
        """Stores a valid refresh token JTI."""
        ...

    @abstractmethod
    async def is_valid(self, jti: str) -> bool:
        """Checks if a refresh token JTI is currently valid."""
        ...

    @abstractmethod
    async def revoke_token(self, jti: str) -> None:
        """Revokes a specific refresh token (used during normal rotation)."""
        ...

    @abstractmethod
    async def revoke_session(self, session_id: str) -> None:
        """Revokes all tokens associated with a session (used on logout or compromise)."""
        ...

    @abstractmethod
    async def is_session_valid(self, session_id: str) -> bool:
        """Checks if a session is still valid."""
        ...
