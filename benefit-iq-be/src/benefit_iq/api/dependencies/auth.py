"""Authentication Dependency Injection Handlers for FastAPI Routes."""

from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from benefit_iq.application.auth.queries.get_current_user import (
    GetCurrentUserHandler,
    GetCurrentUserQuery,
)
from benefit_iq.domain.entities.user import User
from benefit_iq.domain.exceptions.auth_exceptions import AuthDomainException
from benefit_iq.infrastructure.authentication.jwt_service import JWTService
from benefit_iq.infrastructure.authentication.refresh_token_store import RedisRefreshTokenStore

oauth2_scheme = HTTPBearer()


@inject
async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    jwt_service: JWTService = Depends(Provide["token_service"]),
    refresh_token_store: RedisRefreshTokenStore = Depends(Provide["refresh_token_store"]),
) -> UUID:
    """Extracts and validates current authenticated user ID from JWT bearer token."""
    try:
        payload = jwt_service.decode_token(credentials.credentials)
    except AuthDomainException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    if payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if session is still valid (e.g. not logged out)
    is_valid = await refresh_token_store.is_session_valid(payload.session_id)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload.user_id


@inject
async def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    handler: GetCurrentUserHandler = Depends(Provide["get_current_user_handler"]),
) -> User:
    """Retrieves current authenticated User entity."""
    try:
        return await handler.handle(GetCurrentUserQuery(user_id=user_id))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@inject
async def get_current_admin_user(
    user: Annotated[User, Depends(get_current_user)],
    role_repository=Depends(Provide["role_repository"]),
) -> User:
    """Ensures current authenticated user has administrative privileges (Role: ADMIN)."""
    role = await role_repository.get_by_id(user.role_id)
    if not role or not role.is_active or role.name.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Administrative privileges required.",
        )
    return user
