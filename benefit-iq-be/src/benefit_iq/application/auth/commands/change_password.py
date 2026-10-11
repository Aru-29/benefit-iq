"""Change Password Command and Handler for Local and SSO Users."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import structlog

from benefit_iq.application.contracts.auth.email_service import EmailService
from benefit_iq.application.contracts.auth.password_hasher import PasswordHasher
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.exceptions.user_exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ChangePasswordCommand:
    """Command payload for setting or updating a user's password."""

    user_id: UUID
    new_password: str
    current_password: str | None = None


class ChangePasswordHandler:
    """Handler managing password updates for both password-authenticated and SSO users."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        email_service: EmailService,
    ) -> None:
        """Initialize change password handler dependencies."""
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.email_service = email_service

    async def handle(self, command: ChangePasswordCommand) -> None:
        """Updates or sets a password, bypassing current_password check for SSO users without password_hash."""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user or not user.is_active:
            raise UserNotFoundException("User not found or inactive.")

        if user.password_hash is not None:
            # Local password exists -> Require current password verification
            if not command.current_password:
                raise InvalidCredentialsException(
                    "Current password is required to change existing password."
                )
            is_valid = self.password_hasher.verify_password(
                command.current_password, user.password_hash
            )
            if not is_valid:
                logger.warning("change_password_failed_invalid_current", user_id=str(user.id))
                raise InvalidCredentialsException("Current password is not correct.")
        else:
            logger.info("sso_user_setting_initial_password", user_id=str(user.id))

        # Hash & update password
        now = datetime.now(UTC)
        hashed_password = self.password_hasher.hash_password(command.new_password)
        user.password_hash = hashed_password
        user.updated_at = now

        await self.user_repository.update(user)
        await self.email_service.send_password_changed_notification(to_email=user.email)

        logger.info("password_changed_successfully", user_id=str(user.id))
