"""Roles & Access Control (RBAC) Router.

Provides administrative endpoints for listing system roles, creating custom roles,
updating role properties, and deactivating access control rules.
"""
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from benefit_iq.api.schemas.common import (
    ApiResponse,
)
from benefit_iq.api.schemas.lookup import GenericLookupResponse, LookupItem
from benefit_iq.api.schemas.roles import (
    CreateRoleRequest,
    UpdateRoleRequest,
    RoleResponse,
)
from benefit_iq.application.roles.commands.create_role import (
    CreateRoleCommand,
    CreateRoleHandler,
)
from benefit_iq.application.roles.commands.deactivate_role import (
    DeactivateRoleCommand,
    DeactivateRoleHandler,
)
from benefit_iq.application.roles.commands.update_role import (
    UpdateRoleCommand,
    UpdateRoleHandler,
)
from benefit_iq.application.roles.queries.get_role import (
    GetRoleHandler,
    GetRoleQuery,
)
from benefit_iq.application.roles.queries.list_roles import (
    ListRolesHandler,
    ListRolesQuery,
)


from benefit_iq.api.dependencies.auth import get_current_admin_user


router = APIRouter(
    prefix="/roles",
    tags=["Roles & Access Control"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.post(
    "",
    response_model=ApiResponse[RoleResponse],
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_role(
    request: CreateRoleRequest,
    handler: CreateRoleHandler = Depends(
        Provide["create_role_handler"]
    ),
):

    """Async function missing docstring."""
    role = await handler.handle(
        CreateRoleCommand(
            name=request.name,
            description=request.description,
        )
    )

    return ApiResponse(
        success=True,
        data=RoleResponse.model_validate(role),
    )


@router.get(
    "/lookup",
    response_model=ApiResponse[GenericLookupResponse],
)
@inject
async def lookup_roles(
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    handler: ListRolesHandler = Depends(Provide["list_roles_handler"]),
):
    """Admin Only: Paginated & searchable generic role lookup for UI autocompletes."""
    roles = await handler.handle(ListRolesQuery(page=page, page_size=page_size))
    items = []
    for r in roles:
        if search and search.lower() not in r.name.lower() and search.lower() not in (r.description or "").lower():
            continue
        items.append(
            LookupItem(
                id=str(r.id),
                label=r.name.upper(),
                value=str(r.id),
                description=r.description,
            )
        )
    has_more = len(roles) >= page_size
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


@router.get(
    "/{role_id}",
    response_model=ApiResponse[RoleResponse],
)
@inject
async def get_role(
    role_id: UUID,
    handler: GetRoleHandler = Depends(
        Provide["get_role_handler"]
    ),
):

    """Async function missing docstring."""
    role = await handler.handle(
        GetRoleQuery(
            role_id=role_id,
        )
    )

    return ApiResponse(
        success=True,
        data=RoleResponse.model_validate(role),
    )


@router.get(
    "",
    response_model=ApiResponse[
        list[RoleResponse]
    ],
)
@inject
async def list_roles(
    page: int = 1,
    page_size: int = 20,
    handler: ListRolesHandler = Depends(
        Provide["list_roles_handler"]
    ),
):

    """Async function missing docstring."""
    roles = await handler.handle(
        ListRolesQuery(
            page=page,
            page_size=page_size,
        )
    )

    return ApiResponse(
        success=True,
        data=[
            RoleResponse.model_validate(role)
            for role in roles
        ],
    )


@router.put(
    "/{role_id}",
    response_model=ApiResponse[RoleResponse],
)
@inject
async def update_role(
    role_id: UUID,
    request: UpdateRoleRequest,
    handler: UpdateRoleHandler = Depends(
        Provide["update_role_handler"]
    ),
):

    """Async function missing docstring."""
    role = await handler.handle(
        UpdateRoleCommand(
            role_id=role_id,
            name=request.name,
            description=request.description,
            is_active=request.is_active,
        )
    )

    return ApiResponse(
        success=True,
        data=RoleResponse.model_validate(role),
    )


@router.patch(
    "/{role_id}/deactivate",
    response_model=ApiResponse[RoleResponse],
)
@inject
async def deactivate_role(
    role_id: UUID,
    handler: DeactivateRoleHandler = Depends(
        Provide["deactivate_role_handler"]
    ),
):

    """Async function missing docstring."""
    role = await handler.handle(
        DeactivateRoleCommand(
            role_id=role_id,
        )
    )

    return ApiResponse(
        success=True,
        data=RoleResponse.model_validate(role),
    )
