"""
Module missing docstring.
"""
import structlog
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class UpdateProfileCommand:
    """Class missing docstring."""
    user_id: UUID
    first_name: str
    last_name: str
    username: str
    middle_name: str | None = None
    preferred_settings: dict | None = None


class UpdateProfileHandler:

    """Class missing docstring."""
    def __init__(self, user_repository: UserRepository) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository

    async def handle(self, command: UpdateProfileCommand) -> User:
        """Async function missing docstring."""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user or not user.is_active:
            raise UserNotFoundException("User not found or inactive.")

        if user.username != command.username:
            existing_username = await self.user_repository.get_by_username(command.username)
            if existing_username:
                raise UserAlreadyExistsException(f"User with username '{command.username}' already exists.")

        user.first_name = command.first_name
        user.last_name = command.last_name
        user.username = command.username
        user.middle_name = command.middle_name
        user.preferred_settings = command.preferred_settings
        user.updated_at = datetime.now(UTC)

        result = await self.user_repository.update(user)

        logger.info(
            "user_profile_updated",
            user_id=str(user.id),
        )

        return result
