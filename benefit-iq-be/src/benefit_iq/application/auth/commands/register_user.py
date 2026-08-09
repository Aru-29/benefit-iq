"""2-Step OTP User Registration Command and Handler Module."""
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from benefit_iq.application.contracts.auth.email_service import EmailService
from benefit_iq.application.contracts.auth.password_hasher import PasswordHasher
from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.application.contracts.auth.token_service import TokenPair, TokenService
from benefit_iq.application.contracts.repositories.role_repository import RoleRepository
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.enums.auth_provider import AuthProvider
from benefit_iq.domain.enums.system_role import SystemRole
from benefit_iq.domain.exceptions.role_exceptions import RoleNotFoundException
from benefit_iq.domain.exceptions.user_exceptions import (
    InvalidCredentialsException,
    InvalidOtpException,
    UserAlreadyExistsException,
)
from benefit_iq.infrastructure.security.encryption import PasswordEncryptionService
from benefit_iq.infrastructure.security.otp_service import OtpService

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RegisterUserCommand:
    """Command payload for initiating user registration."""

    email: str
    password: str
    first_name: str
    last_name: str
    username: str
    middle_name: str | None = None


@dataclass(frozen=True)
class VerifyRegistrationOtpCommand:
    """Command payload for verifying registration OTP code."""

    email: str
    otp: str


class RegisterUserHandler:
    """Handler managing 2-Step OTP registration flow."""

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        password_hasher: PasswordHasher,
        email_service: EmailService,
        otp_service: OtpService,
        password_encryption: PasswordEncryptionService | None = None,
        token_service: TokenService | None = None,
        refresh_token_store: RefreshTokenStore | None = None,
    ) -> None:
        """Initialize registration handler dependencies."""
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.password_hasher = password_hasher
        self.email_service = email_service
        self.otp_service = otp_service
        self.password_encryption = password_encryption
        self.token_service = token_service
        self.refresh_token_store = refresh_token_store

    async def handle(self, command: RegisterUserCommand) -> dict[str, str]:
        """Step 1: Validates user details, hashes password, stores pending registration, and emails OTP code."""
        existing_email = await self.user_repository.get_by_email(command.email)
        if existing_email:
            raise UserAlreadyExistsException(f"User with email '{command.email}' already exists.")

        existing_username = await self.user_repository.get_by_username(command.username)
        if existing_username:
            raise UserAlreadyExistsException(f"User with username '{command.username}' already exists.")

        customer_role = await self.role_repository.get_by_name(SystemRole.CUSTOMER.value)
        if not customer_role:
            raise RoleNotFoundException("Default CUSTOMER role not found in the system.")

        # Decrypt password if encrypted from frontend
        plain_password = command.password
        if hasattr(self, 'password_encryption') and getattr(self, 'password_encryption') is not None:
            try:
                plain_password = self.password_encryption.decrypt(command.password)
            except Exception:
                try:
                    plain_password = self.password_encryption.decrypt_alphanumeric(command.password)
                except Exception:
                    plain_password = command.password

        hashed_password = self.password_hasher.hash_password(plain_password)

        pending_data = {
            "username": command.username,
            "first_name": command.first_name,
            "middle_name": command.middle_name,
            "last_name": command.last_name,
            "email": command.email,
            "password_hash": hashed_password,
            "role_id": str(customer_role.id),
        }

        # Store pending registration payload in Redis
        await self.otp_service.store_pending_registration(command.email, pending_data)

        # Generate & send OTP email
        otp = await self.otp_service.generate_otp(purpose="registration", key=command.email)
        await self.email_service.send_otp_email(to_email=command.email, otp=otp, purpose="registration")

        logger.info("registration_otp_sent", email=command.email)
        return {"message": "Registration OTP code sent to your email. Please verify to complete account setup."}

    async def handle_verify_otp(self, command: VerifyRegistrationOtpCommand) -> TokenPair:
        """Step 2: Verifies registration OTP code, persists user account, and issues JWT tokens."""
        is_valid = await self.otp_service.verify_otp(
            purpose="registration", key=command.email, submitted_otp=command.otp
        )
        if not is_valid:
            raise InvalidOtpException("Invalid or expired OTP code.")

        pending_data = await self.otp_service.get_pending_registration(command.email)
        if not pending_data:
            raise InvalidOtpException("Registration session expired. Please register again.")

        role_id_raw = pending_data.get("role_id")
        role_id_val = UUID(role_id_raw) if isinstance(role_id_raw, str) else (role_id_raw or uuid4())

        now = datetime.now(UTC)
        user = User(
            id=uuid4(),
            username=pending_data["username"],
            first_name=pending_data["first_name"],
            middle_name=pending_data.get("middle_name"),
            last_name=pending_data["last_name"],
            email=pending_data["email"],
            password_hash=pending_data["password_hash"],
            role_id=role_id_val,
            authentication_provider=AuthProvider.LOCAL,
            external_provider_id=None,
            is_active=True,
            is_email_verified=True,
            preferred_settings=None,
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )

        result = await self.user_repository.create(user)
        await self.otp_service.delete_pending_registration(command.email)

        session_id = uuid4()
        if self.token_service:
            token_pair = self.token_service.generate_token_pair(
                user_id=result.id,
                role_id=result.role_id,
                session_id=str(session_id),
            )
            if self.refresh_token_store:
                refresh_payload = self.token_service.decode_token(token_pair.refresh_token)
                refresh_ttl = getattr(self.token_service, 'refresh_token_expire_days', 7) * 86400
                await self.refresh_token_store.store_token(
                    jti=refresh_payload.jti,
                    user_id=str(result.id),
                    session_id=str(session_id),
                    expires_in=refresh_ttl,
                )
        else:
            token_pair = TokenPair(access_token="", refresh_token="", expires_in=3600)

        logger.info("user_registered_after_otp_verification", user_id=str(result.id))
        return token_pair
