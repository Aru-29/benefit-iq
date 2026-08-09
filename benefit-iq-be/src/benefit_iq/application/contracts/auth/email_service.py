"""
Module missing docstring.
"""
from abc import ABC, abstractmethod


class EmailService(ABC):
    """Class missing docstring."""

    @abstractmethod
    async def send_verification_email(self, to_email: str, token: str) -> None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def send_password_reset_email(self, to_email: str, token: str) -> None:
        """Async function missing docstring."""
        ...

    @abstractmethod
    async def send_password_changed_notification(self, to_email: str) -> None:
        """Sends security alert notification when password is changed."""
        ...

    @abstractmethod
    async def send_otp_email(self, to_email: str, otp: str, purpose: str) -> None:
        """Sends a 2-Step OTP verification email for registration or login."""
        ...
