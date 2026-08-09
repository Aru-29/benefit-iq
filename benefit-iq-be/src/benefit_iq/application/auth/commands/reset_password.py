"""
Module missing docstring.
"""
import structlog
from dataclasses import dataclass

from benefit_iq.application.contracts.auth.password_hasher import PasswordHasher
from benefit_iq.application.contracts.auth.token_service import TokenService
from benefit_iq.application.contracts.auth.email_service import EmailService
from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.exceptions.auth_exceptions import TokenInvalidException
from benefit_iq.domain.exceptions.user_exceptions import UserNotFoundException


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ResetPasswordCommand:
    """Class missing docstring."""
    token: str
    new_password: str


class ResetPasswordHandler:

    """Class missing docstring."""
    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
        password_hasher: PasswordHasher,
        email_service: EmailService,
        refresh_token_store: RefreshTokenStore,
    ) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository
        self.token_service = token_service
        self.password_hasher = password_hasher
        self.email_service = email_service
        self.refresh_token_store = refresh_token_store

    async def handle(self, command: ResetPasswordCommand) -> None:
        """Async function missing docstring."""
        try:
            user_id = self.token_service.decode_password_reset_token(command.token)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise TokenInvalidException(f"Invalid or expired password reset token. {e}") from e

        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise UserNotFoundException("User not found or inactive.")

        hashed_password = self.password_hasher.hash_password(command.new_password)
        user.password_hash = hashed_password

        await self.user_repository.update(user)

        # Invalidate all existing sessions since the password was reset
        # Implementation depends on how we query sessions by user_id in Redis.
        # This will be handled in the infrastructure layer.

        await self.email_service.send_password_changed_notification(
            to_email=user.email
        )

        logger.info(
            "password_reset_completed",
            user_id=str(user.id),
        )
