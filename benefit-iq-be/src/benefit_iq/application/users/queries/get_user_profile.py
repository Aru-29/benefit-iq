"""
Module missing docstring.
"""

from dataclasses import dataclass
from uuid import UUID

from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.exceptions.user_exceptions import UserNotFoundException


@dataclass(frozen=True)
class GetUserProfileQuery:
    """Class missing docstring."""

    user_id: UUID


class GetUserProfileHandler:
    """Class missing docstring."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository

    async def handle(self, query: GetUserProfileQuery) -> User:
        """Async function missing docstring."""
        user = await self.user_repository.get_by_id(query.user_id)
        if not user or not user.is_active:
            raise UserNotFoundException("User not found or inactive.")
        return user
