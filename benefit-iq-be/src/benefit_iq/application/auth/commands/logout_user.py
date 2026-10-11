"""
Module missing docstring.
"""

from dataclasses import dataclass

import structlog

from benefit_iq.application.contracts.auth.refresh_token_store import RefreshTokenStore
from benefit_iq.application.contracts.auth.token_service import TokenService

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class LogoutUserCommand:
    """Class missing docstring."""

    refresh_token: str


class LogoutUserHandler:
    """Class missing docstring."""

    def __init__(
        self,
        token_service: TokenService,
        refresh_token_store: RefreshTokenStore,
    ) -> None:
        """Function missing docstring."""
        self.token_service = token_service
        self.refresh_token_store = refresh_token_store

    async def handle(self, command: LogoutUserCommand) -> None:
        """Async function missing docstring."""
        try:
            payload = self.token_service.decode_token(command.refresh_token)
        except Exception:  # pylint: disable=broad-exception-caught
            # If the token is invalid, we don't care, we just do nothing and return success.
            return

        if payload.token_type != "refresh":
            return

        await self.refresh_token_store.revoke_session(payload.session_id)

        logger.info(
            "user_logged_out",
            user_id=str(payload.user_id),
            session_id=payload.session_id,
        )
