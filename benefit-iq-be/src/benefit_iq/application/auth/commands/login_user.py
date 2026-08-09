"""2-Step 2FA OTP Login User Command and Handler Module."""
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from benefit_iq.application.contracts.auth.email_service import EmailService
from benefit_iq.application.contracts.auth.password_hasher import PasswordHasher
from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.application.contracts.auth.token_service import TokenPair, TokenService
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.exceptions.user_exceptions import (
    InvalidCredentialsException,
    InvalidOtpException,
    UserDomainException,
)
from benefit_iq.infrastructure.security.encryption import PasswordEncryptionService
from benefit_iq.infrastructure.security.otp_service import OtpService
from opentelemetry import trace

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass(frozen=True)
class LoginUserCommand:
    """Command payload for initiating 2-Step login authentication."""

    email: str
    password: str
    user_agent: str | None = None
    ip_address: str | None = None


@dataclass(frozen=True)
class VerifyLoginOtpCommand:
    """Command payload for verifying login 2FA OTP code and issuing JWT tokens."""

    email: str
    otp: str
    user_agent: str | None = None
    ip_address: str | None = None


class LoginUserHandler:
    """Handler managing 2-Step 2FA OTP login authentication flow."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        refresh_token_store: RefreshTokenStore,
        email_service: EmailService,
        otp_service: OtpService,
        password_encryption: PasswordEncryptionService | None = None,
    ) -> None:
        """Initialize login handler dependencies."""
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.refresh_token_store = refresh_token_store
        self.email_service = email_service
        self.otp_service = otp_service
        self.password_encryption = password_encryption

    async def handle(self, command: LoginUserCommand) -> dict[str, str]:
        """Step 1: Decrypts password, verifies Argon2id hash, and sends 2FA login OTP email."""
        with tracer.start_as_current_span("login_user_step_1") as span:
            user = await self.user_repository.get_by_email(command.email)
            if not user or not user.is_active or not user.password_hash:
                logger.warning(
                    "login_failed",
                    email=command.email,
                    reason="user_not_found_or_inactive_or_no_password",
                )
                span.set_attribute("login.result", "failed_user_not_found")
                raise InvalidCredentialsException("Invalid email or password.")

            # Decrypt password if encrypted from frontend
            plain_password = command.password
            if self.password_encryption:
                try:
                    plain_password = self.password_encryption.decrypt(command.password)
                except Exception:  # pylint: disable=broad-exception-caught
                    try:
                        plain_password = self.password_encryption.decrypt_alphanumeric(command.password)
                    except Exception:  # pylint: disable=broad-exception-caught
                        plain_password = command.password

            is_valid = self.password_hasher.verify_password(plain_password, user.password_hash)
            if not is_valid:
                logger.warning("login_failed", email=command.email, reason="invalid_password")
                span.set_attribute("login.result", "failed_invalid_password")
                raise InvalidCredentialsException("Invalid email or password.")

            # Generate & send 2FA Login OTP code
            otp = await self.otp_service.generate_otp(purpose="login", key=command.email)
            await self.email_service.send_otp_email(to_email=command.email, otp=otp, purpose="login")

            logger.info("login_otp_sent", email=command.email)
            span.set_attribute("login.result", "success_otp_sent")
            return {"message": "Login 2FA OTP code sent to your email. Please verify to receive access tokens."}

    async def handle_verify_login_otp(
        self, command: VerifyLoginOtpCommand
    ) -> TokenPair:
        """Step 2: Verifies 2FA login OTP code and issues JWT access & refresh token pair."""
        with tracer.start_as_current_span("login_user_step_2") as span:
            is_valid = await self.otp_service.verify_otp(
                purpose="login", key=command.email, submitted_otp=command.otp
            )
            if not is_valid:
                span.set_attribute("login.result", "failed_invalid_otp")
                raise InvalidOtpException("Invalid or expired 2FA OTP code.")

            user = await self.user_repository.get_by_email(command.email)
            if not user or not user.is_active:
                span.set_attribute("login.result", "failed_inactive_user")
                raise UserDomainException("User account is inactive or disabled.")

            now = datetime.now(UTC)
            session_id = uuid4()
            token_pair = self.token_service.generate_token_pair(
                user_id=user.id,
                role_id=user.role_id,
                session_id=str(session_id),
            )

            refresh_payload = self.token_service.decode_token(token_pair.refresh_token)
            refresh_ttl = self.token_service.refresh_token_expire_days * 86400
            await self.refresh_token_store.store_token(
                jti=refresh_payload.jti,
                user_id=str(user.id),
                session_id=str(session_id),
                expires_in=refresh_ttl,
            )

            user.last_login_at = now
            await self.user_repository.update(user)

            logger.info(
                "login_completed_after_otp_verification",
                user_id=str(user.id),
                session_id=str(session_id),
            )
            span.set_attribute("login.result", "success")
            return token_pair
