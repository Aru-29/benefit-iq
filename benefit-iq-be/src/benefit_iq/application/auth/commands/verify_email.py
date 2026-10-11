"""
Module missing docstring.
"""

from dataclasses import dataclass

import structlog

from benefit_iq.application.contracts.auth.token_service import TokenService
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.exceptions.auth_exceptions import TokenInvalidException
from benefit_iq.domain.exceptions.user_exceptions import UserNotFoundException

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class VerifyEmailCommand:
    """Class missing docstring."""

    token: str


class VerifyEmailHandler:
    """Class missing docstring."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
    ) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository
        self.token_service = token_service

    async def handle(self, command: VerifyEmailCommand) -> None:
        """Async function missing docstring."""
        try:
            user_id = self.token_service.decode_verification_token(command.token)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise TokenInvalidException(f"Invalid or expired verification token. {e}") from e

        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise UserNotFoundException("User not found or inactive.")

        if user.is_email_verified:
            # Already verified, idempotent
            return

        user.verify_email()
        await self.user_repository.update(user)

        logger.info(
            "email_verified",
            user_id=str(user.id),
        )
