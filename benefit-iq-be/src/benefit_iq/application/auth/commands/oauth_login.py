"""
Module missing docstring.
"""
import structlog
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from benefit_iq.application.contracts.auth.token_service import TokenService, TokenPair
from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.application.contracts.auth.identity_provider import ExternalIdentityProvider
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.application.contracts.repositories.role_repository import RoleRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.enums.auth_provider import AuthProvider
from benefit_iq.domain.enums.system_role import SystemRole
from benefit_iq.domain.exceptions.user_exceptions import InvalidCredentialsException, UserDomainException
from benefit_iq.domain.exceptions.role_exceptions import RoleNotFoundException


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class OAuthLoginCommand:
    """Command payload for processing Google/Microsoft OAuth2 login."""

    provider_name: str
    code: str | None = None
    token: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None


class OAuthLoginHandler:
    """Handler managing Google and Microsoft OAuth2 authentication."""

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        token_service: TokenService,
        identity_providers: dict[str, ExternalIdentityProvider],
        refresh_token_store: RefreshTokenStore,
    ) -> None:
        """Initialize OAuth login handler dependencies."""
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.token_service = token_service
        self.identity_providers = identity_providers
        self.refresh_token_store = refresh_token_store

    async def handle(self, command: OAuthLoginCommand) -> TokenPair:
        """Validates OAuth provider token or code and issues Benefit IQ JWT token pair."""
        if command.provider_name not in self.identity_providers:
            raise UserDomainException(
                f"Unsupported identity provider: {command.provider_name}"
            )

        provider = self.identity_providers[command.provider_name]
        try:
            if command.token:
                profile = await provider.validate_token_and_get_profile(command.token)
            elif command.code:
                profile = await provider.exchange_code_for_profile(command.code)
            else:
                raise UserDomainException("Either OAuth code or token must be provided.")
        except UserDomainException:
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("oauth_exchange_failed", provider=command.provider_name, error=str(e))
            raise UserDomainException("OAuth authorization failed. Please try signing in again.") from e

        user = await self.user_repository.get_by_external_id(
            provider=command.provider_name,
            external_id=profile.external_id
        )

        now = datetime.now(UTC)

        if not user:
            # Check if user with same email already exists
            user_by_email = await self.user_repository.get_by_email(profile.email)
            if user_by_email:
                # Link account
                user = user_by_email
                user.external_provider_id = profile.external_id
                user.authentication_provider = AuthProvider(command.provider_name)
                user.update_last_login(now)
                await self.user_repository.update(user)
            else:
                # Register new OAuth user
                customer_role = await self.role_repository.get_by_name(SystemRole.CUSTOMER.value)
                if not customer_role:
                    raise RoleNotFoundException("Default CUSTOMER role not found.")

                # Generate a random username if needed, or use prefix of email
                base_username = profile.email.split("@")[0]
                username = f"{base_username}_{str(uuid4())[:8]}"

                user = User(
                    id=uuid4(),
                    username=username,
                    first_name=profile.first_name,
                    middle_name=None,
                    last_name=profile.last_name,
                    email=profile.email,
                    password_hash=None, # No local password
                    role_id=customer_role.id,
                    authentication_provider=AuthProvider(command.provider_name),
                    external_provider_id=profile.external_id,
                    is_active=True,
                    is_email_verified=profile.is_email_verified,
                    preferred_settings=None,
                    created_at=now,
                    updated_at=now,
                    last_login_at=now,
                )
                await self.user_repository.create(user)
        else:
            if not user.is_active:
                raise InvalidCredentialsException("User account is inactive.")
            user.update_last_login(now)
            await self.user_repository.update(user)

        session_id = str(uuid4())
        token_pair = self.token_service.generate_token_pair(
            user_id=user.id,
            role_id=user.role_id,
            session_id=session_id
        )

        refresh_payload = self.token_service.decode_token(token_pair.refresh_token)
        expires_in = int((refresh_payload.exp.replace(tzinfo=UTC) - now).total_seconds())

        await self.refresh_token_store.store_token(
            jti=refresh_payload.jti,
            user_id=str(user.id),
            session_id=session_id,
            expires_in=expires_in
        )

        logger.info(
            "oauth_user_logged_in",
            user_id=str(user.id),
            provider=command.provider_name,
            session_id=session_id,
        )

        return token_pair
