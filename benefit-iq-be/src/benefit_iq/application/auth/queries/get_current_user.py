"""
Module missing docstring.
"""
from dataclasses import dataclass
from uuid import UUID

from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.exceptions.user_exceptions import UserNotFoundException


@dataclass(frozen=True)
class GetCurrentUserQuery:
    """Class missing docstring."""
    user_id: UUID


class GetCurrentUserHandler:

    """Class missing docstring."""
    def __init__(self, user_repository: UserRepository) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository

    async def handle(self, query: GetCurrentUserQuery) -> User:
        """Async function missing docstring."""
        user = await self.user_repository.get_by_id(query.user_id)
        if not user:
            raise UserNotFoundException("User not found.")
        return user
