"""
Module missing docstring.
"""
import structlog
from dataclasses import dataclass

from benefit_iq.application.contracts.auth.token_service import TokenService
from benefit_iq.application.contracts.auth.email_service import EmailService
from benefit_iq.application.contracts.repositories.user_repository import UserRepository


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ForgotPasswordCommand:
    """Class missing docstring."""
    email: str


class ForgotPasswordHandler:

    """Class missing docstring."""
    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
        email_service: EmailService,
    ) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository
        self.token_service = token_service
        self.email_service = email_service

    async def handle(self, command: ForgotPasswordCommand) -> None:
        """Async function missing docstring."""
        user = await self.user_repository.get_by_email(command.email)

        # We don't throw an error if the user doesn't exist to prevent email enumeration.
        if not user or not user.is_active:
            logger.info("forgot_password_requested_unknown_user", email=command.email)
            return

        token = self.token_service.generate_password_reset_token(user.id)

        await self.email_service.send_password_reset_email(
            to_email=user.email,
            token=token,
        )

        logger.info(
            "password_reset_email_sent",
            user_id=str(user.id),
        )
