"""Global Exception Handlers for FastAPI Application.

Translates domain exceptions (AuthDomainException, UserDomainException, RoleException)
and uncaught system exceptions into standardized ApiResponse JSON structures.
"""
# pylint: disable=unused-argument
from fastapi import Request, status
from fastapi.responses import JSONResponse

from benefit_iq.api.schemas.common import ApiResponse, ErrorDetail
from benefit_iq.domain.exceptions.role_exceptions import (
    InvalidRoleNameException,
    RoleAlreadyExistsException,
    RoleNotFoundException,
)
from benefit_iq.domain.exceptions.auth_exceptions import (
    AuthDomainException,
    TokenInvalidException,
    TokenExpiredException,
)
from benefit_iq.domain.exceptions.user_exceptions import (
    UserDomainException,
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
)


async def role_not_found_handler(
    request: Request,
    exc: RoleNotFoundException,
) -> JSONResponse:
    """Async function missing docstring."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ApiResponse(
            success=False,
            error=ErrorDetail(message=str(exc), code="role_not_found"),
        ).model_dump(),
    )


async def role_conflict_handler(
    request: Request,
    exc: RoleAlreadyExistsException,
) -> JSONResponse:
    """Async function missing docstring."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ApiResponse(
            success=False,
            error=ErrorDetail(message=str(exc), code="role_conflict"),
        ).model_dump(),
    )


async def invalid_role_handler(
    request: Request,
    exc: InvalidRoleNameException,
) -> JSONResponse:
    """Async function missing docstring."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ApiResponse(
            success=False,
            error=ErrorDetail(message=str(exc), code="invalid_role"),
        ).model_dump(),
    )


async def auth_exception_handler(
    request: Request,
    exc: AuthDomainException,
) -> JSONResponse:
    """Async function missing docstring."""
    status_code = status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, TokenExpiredException):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, TokenInvalidException):
        status_code = status.HTTP_401_UNAUTHORIZED

    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(
            success=False,
            error=ErrorDetail(message=str(exc), code="auth_error"),
        ).model_dump(),
    )


async def user_exception_handler(
    request: Request,
    exc: UserDomainException,
) -> JSONResponse:
    """Async function missing docstring."""
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, UserNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, UserAlreadyExistsException):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, InvalidCredentialsException):
        status_code = status.HTTP_401_UNAUTHORIZED

    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(
            success=False,
            error=ErrorDetail(message=str(exc), code="user_error"),
        ).model_dump(),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Async function missing docstring."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(
            success=False,
            error=ErrorDetail(message="An internal server error occurred.", code="internal_server_error"),
        ).model_dump(),
    )
