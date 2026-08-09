"""
Module missing docstring.
"""
import structlog
from dataclasses import dataclass
from datetime import UTC, datetime

from benefit_iq.application.contracts.auth.token_service import TokenService, TokenPair
from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.exceptions.auth_exceptions import (
    TokenInvalidException,
    RefreshTokenReusedException,
    TokenFamilyRevokedException,
)
from benefit_iq.domain.exceptions.user_exceptions import UserNotFoundException


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RefreshTokenCommand:
    """Class missing docstring."""
    refresh_token: str


class RefreshTokenHandler:

    """Class missing docstring."""
    def __init__(
        self,
        token_service: TokenService,
        refresh_token_store: RefreshTokenStore,
        user_repository: UserRepository,
    ) -> None:
        """Function missing docstring."""
        self.token_service = token_service
        self.refresh_token_store = refresh_token_store
        self.user_repository = user_repository

    async def handle(self, command: RefreshTokenCommand) -> TokenPair:
        """Async function missing docstring."""
        try:
            payload = self.token_service.decode_token(command.refresh_token)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise TokenInvalidException(f"Invalid refresh token: {e}") from e

        if payload.token_type != "refresh":
            raise TokenInvalidException("Expected a refresh token.")

        is_session_valid = await self.refresh_token_store.is_session_valid(payload.session_id)
        if not is_session_valid:
            raise TokenFamilyRevokedException("Session has been revoked.")

        is_token_valid = await self.refresh_token_store.is_valid(payload.jti)
        if not is_token_valid:
            # Token is valid cryptographically but not in the store -> Reuse detected!
            logger.warning(
                "refresh_token_reuse_detected",
                user_id=str(payload.user_id),
                session_id=payload.session_id,
                jti=payload.jti,
            )
            await self.refresh_token_store.revoke_session(payload.session_id)
            raise RefreshTokenReusedException("Refresh token reuse detected. Session revoked.")

        user = await self.user_repository.get_by_id(payload.user_id)
        if not user or not user.is_active:
            raise UserNotFoundException("User not found or inactive.")

        # Revoke the used refresh token
        await self.refresh_token_store.revoke_token(payload.jti)

        # Generate a new token pair
        token_pair = self.token_service.generate_token_pair(
            user_id=user.id,
            role_id=user.role_id,
            session_id=payload.session_id,
        )

        new_payload = self.token_service.decode_token(token_pair.refresh_token)
        await self.refresh_token_store.store_token(
            jti=new_payload.jti,
            user_id=str(user.id),
            session_id=payload.session_id,
            expires_in=token_pair.expires_in,
        )

        logger.info(
            "token_refreshed",
            user_id=str(user.id),
            session_id=payload.session_id,
        )

        return token_pair
