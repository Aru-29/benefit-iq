"""User Profile & Management Router.

Provides endpoints for authenticated user profile retrieval, account settings updates,
and administrative user management (listing, fetching, updating, and deleting users).
"""
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from benefit_iq.api.dependencies.auth import get_current_user, get_current_admin_user
from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.api.schemas.lookup import GenericLookupResponse, LookupItem
from benefit_iq.api.schemas.query import QueryRequest, QueryResponse
from benefit_iq.api.schemas.users import (
    UserProfileResponse,
    UpdateProfileRequest,
)
from benefit_iq.application.users.commands.update_profile import (
    UpdateProfileCommand,
    UpdateProfileHandler,
)
from benefit_iq.application.users.queries.get_user_profile import (
    GetUserProfileQuery,
    GetUserProfileHandler,
)
from benefit_iq.domain.entities.user import User

router = APIRouter(
    prefix="/users",
    tags=["User Profile & Management"],
)


@router.get("/me", response_model=ApiResponse[UserProfileResponse])
@inject
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    role_repository=Depends(Provide["role_repository"]),
):
    """Retrieves profile data for the currently authenticated user."""
    role = await role_repository.get_by_id(current_user.role_id)
    role_name = role.name.upper() if role else "CUSTOMER"
    return ApiResponse(
        success=True,
        data=UserProfileResponse(
            id=current_user.id,
            username=current_user.username,
            first_name=current_user.first_name,
            middle_name=current_user.middle_name,
            last_name=current_user.last_name,
            email=current_user.email,
            role_id=current_user.role_id,
            role_name=role_name,
            is_active=current_user.is_active,
            is_email_verified=current_user.is_email_verified,
            preferred_settings=current_user.preferred_settings,
            created_at=current_user.created_at,
            last_login_at=current_user.last_login_at,
        ),
    )


@router.put("/me", response_model=ApiResponse[UserProfileResponse])
@inject
async def update_my_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    handler: UpdateProfileHandler = Depends(Provide["update_profile_handler"]),
):
    """Updates profile data for the currently authenticated user."""
    user = await handler.handle(
        UpdateProfileCommand(
            user_id=current_user.id,
            first_name=request.first_name,
            last_name=request.last_name,
            username=request.username,
            middle_name=request.middle_name,
            preferred_settings=request.preferred_settings,
        )
    )

    return ApiResponse(
        success=True,
        data=UserProfileResponse(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            role_id=user.role_id,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            preferred_settings=user.preferred_settings,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        ),
    )


@router.post("/query", response_model=ApiResponse[QueryResponse])
@inject
async def query_users(
    request: QueryRequest,
    _admin: User = Depends(get_current_admin_user),
    user_repository=Depends(Provide["user_repository"]),
):
    """Admin Only: Advanced datatype-aware query & search across system users."""
    response = await user_repository.query_generic(request)
    return ApiResponse(success=True, data=response)


@router.get("/lookup", response_model=ApiResponse[GenericLookupResponse])
@inject
async def lookup_users(
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    user_repository=Depends(Provide["user_repository"]),
    _admin: User = Depends(get_current_admin_user),
):
    """Admin Only: Paginated & searchable generic user lookup for UI autocompletes."""
    users = await user_repository.list(offset=(page - 1) * page_size, limit=page_size)
    items = []
    for u in users:
        full_name = f"{u.first_name} {u.last_name}".strip()
        if search and search.lower() not in full_name.lower() and search.lower() not in u.email.lower():
            continue
        items.append(
            LookupItem(
                id=str(u.id),
                label=f"{full_name} ({u.email})",
                value=str(u.id),
                description=u.email,
            )
        )
    has_more = len(users) >= page_size
    return ApiResponse(
        success=True,
        data=GenericLookupResponse(
            items=items,
            total=len(items),
            page=page,
            page_size=page_size,
            has_more=has_more,
        ),
    )


@router.get("", response_model=ApiResponse[list[UserProfileResponse]])
@inject
async def list_users(
    offset: int = 0,
    limit: int = 50,
    _admin: User = Depends(get_current_admin_user),
    user_repository=Depends(Provide["user_repository"]),
):
    """Admin Only: Lists system users with pagination."""
    users = await user_repository.list(offset=offset, limit=limit)
    profiles = [
        UserProfileResponse(
            id=u.id,
            username=u.username,
            first_name=u.first_name,
            middle_name=u.middle_name,
            last_name=u.last_name,
            email=u.email,
            role_id=u.role_id,
            is_active=u.is_active,
            is_email_verified=u.is_email_verified,
            preferred_settings=u.preferred_settings,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
        )
        for u in users
    ]
    return ApiResponse(success=True, data=profiles)


@router.get("/{user_id}", response_model=ApiResponse[UserProfileResponse])
@inject
async def get_user_by_id(
    user_id: UUID,
    _admin: User = Depends(get_current_admin_user),
    handler: GetUserProfileHandler = Depends(Provide["get_user_profile_handler"]),
):
    """Admin Only: Retrieves user profile by unique user ID."""
    try:
        user = await handler.handle(GetUserProfileQuery(user_id=user_id))
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        ) from e

    return ApiResponse(
        success=True,
        data=UserProfileResponse(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            role_id=user.role_id,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            preferred_settings=user.preferred_settings,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        ),
    )


@router.put("/{user_id}", response_model=ApiResponse[UserProfileResponse])
@inject
async def update_user_by_id(
    user_id: UUID,
    request: UpdateProfileRequest,
    _admin: User = Depends(get_current_admin_user),
    handler: UpdateProfileHandler = Depends(Provide["update_profile_handler"]),
):
    """Admin Only: Updates any user profile by user ID."""
    user = await handler.handle(
        UpdateProfileCommand(
            user_id=user_id,
            first_name=request.first_name,
            last_name=request.last_name,
            username=request.username,
            middle_name=request.middle_name,
            preferred_settings=request.preferred_settings,
        )
    )

    return ApiResponse(
        success=True,
        data=UserProfileResponse(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            role_id=user.role_id,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            preferred_settings=user.preferred_settings,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        ),
    )


@router.delete("/{user_id}", response_model=ApiResponse[dict])
@inject
async def delete_user(
    user_id: UUID,
    _admin: User = Depends(get_current_admin_user),
    user_repository=Depends(Provide["user_repository"]),
):
    """Admin Only: Soft deletes/deactivates a user account by ID."""
    success = await user_repository.delete(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already deleted.",
        )
    return ApiResponse(
        success=True,
        data={"message": f"User {user_id} deleted successfully."},
    )
