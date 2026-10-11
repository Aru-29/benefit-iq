"""
Module missing docstring.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from benefit_iq.application.contracts.auth.password_hasher import PasswordHasher
from benefit_iq.application.contracts.repositories.role_repository import RoleRepository
from benefit_iq.application.contracts.repositories.user_repository import UserRepository
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.enums.auth_provider import AuthProvider
from benefit_iq.domain.exceptions.role_exceptions import RoleNotFoundException
from benefit_iq.domain.exceptions.user_exceptions import UserAlreadyExistsException

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CreateUserCommand:
    """Class missing docstring."""

    email: str
    password: str
    first_name: str
    last_name: str
    username: str
    role_id: UUID
    middle_name: str | None = None
    is_active: bool = True
    is_email_verified: bool = False


class CreateUserHandler:
    """Class missing docstring."""

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        """Function missing docstring."""
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.password_hasher = password_hasher

    async def handle(self, command: CreateUserCommand) -> User:
        """Async function missing docstring."""
        existing_email = await self.user_repository.get_by_email(command.email)
        if existing_email:
            raise UserAlreadyExistsException(f"User with email '{command.email}' already exists.")

        existing_username = await self.user_repository.get_by_username(command.username)
        if existing_username:
            raise UserAlreadyExistsException(
                f"User with username '{command.username}' already exists."
            )

        role = await self.role_repository.get_by_id(command.role_id)
        if not role:
            raise RoleNotFoundException("Role not found.")

        hashed_password = self.password_hasher.hash_password(command.password)
        now = datetime.now(UTC)

        user = User(
            id=uuid4(),
            username=command.username,
            first_name=command.first_name,
            middle_name=command.middle_name,
            last_name=command.last_name,
            email=command.email,
            password_hash=hashed_password,
            role_id=command.role_id,
            authentication_provider=AuthProvider.LOCAL,
            external_provider_id=None,
            is_active=command.is_active,
            is_email_verified=command.is_email_verified,
            preferred_settings=None,
            created_at=now,
            updated_at=now,
            last_login_at=None,
        )

        result = await self.user_repository.create(user)

        logger.info(
            "user_created_by_admin",
            user_id=str(result.id),
        )

        return result
