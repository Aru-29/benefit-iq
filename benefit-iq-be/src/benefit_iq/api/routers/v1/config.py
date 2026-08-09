"""Dynamic Application Configuration API Router.

Provides administrative REST API endpoints for managing system key-value configuration
properties, storing secrets in OpenBao Vault, and updating Redis cache.
"""
# pylint: disable=line-too-long
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from benefit_iq.api.dependencies.auth import get_current_admin_user
from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.api.schemas.query import QueryRequest, QueryResponse
from benefit_iq.api.schemas.config import (
    AppConfigResponse,
    CreateConfigRequest,
    UpdateConfigRequest,
)
from benefit_iq.infrastructure.configuration.app_config_service import AppConfigService

router = APIRouter(
    prefix="/config",
    tags=["Application Configuration"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.post("", response_model=ApiResponse[AppConfigResponse], status_code=status.HTTP_201_CREATED)
@inject
async def create_config(
    request: CreateConfigRequest,
    config_service: AppConfigService = Depends(Provide["app_config_service"]),
):
    """Admin Only: Creates or sets an application configuration key."""
    saved = await config_service.set_config(
        config_key=request.config_key,
        value=request.value,
        is_secret=request.is_secret,
        secret_path=request.secret_path,
        secret_key=request.secret_key,
        description=request.description,
        app=request.application,
        env=request.environment,
    )
    return ApiResponse(
        success=True,
        data=AppConfigResponse(
            id=saved.id,
            application=saved.application,
            environment=saved.environment,
            config_key=saved.config_key,
            config_value=saved.config_value,
            is_secret=saved.is_secret,
            secret_path=saved.secret_path,
            secret_key=saved.secret_key,
            description=saved.description,
            is_active=saved.is_active,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        ),
    )


@router.post("/query", response_model=ApiResponse[QueryResponse])
@inject
async def query_configs(
    request: QueryRequest,
    config_service: AppConfigService = Depends(Provide["app_config_service"]),
):
    """Admin Only: Query configuration items with filters, sorting, and pagination."""
    res = await config_service.repository.query_generic(request)
    return ApiResponse(success=True, data=res)


@router.get("", response_model=ApiResponse[list[AppConfigResponse]])
@inject
async def list_configs(
    app: str = "benefit-iq-be",
    env: str = "development",
    config_service: AppConfigService = Depends(Provide["app_config_service"]),
):
    """Admin Only: Lists all active application configuration metadata entries."""
    configs = await config_service.list_configs(app=app, env=env)
    res = [
        AppConfigResponse(
            id=c.id,
            application=c.application,
            environment=c.environment,
            config_key=c.config_key,
            config_value=c.config_value,
            is_secret=c.is_secret,
            secret_path=c.secret_path,
            secret_key=c.secret_key,
            description=c.description,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs
    ]
    return ApiResponse(success=True, data=res)


@router.get("/{config_key}", response_model=ApiResponse[dict])
@inject
async def get_config_value(
    config_key: str,
    app: str = "benefit-iq-be",
    env: str = "development",
    config_service: AppConfigService = Depends(Provide["app_config_service"]),
):
    """Admin Only: Retrieves a resolved configuration value (fetches from Redis -> ClickHouse -> OpenBao)."""
    val = await config_service.get_config(config_key, app=app, env=env)
    if val is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key '{config_key}' not found.",
        )
    return ApiResponse(
        success=True,
        data={"config_key": config_key, "value": val},
    )


@router.put("/{config_key}", response_model=ApiResponse[AppConfigResponse])
@inject
async def update_config(
    config_key: str,
    request: UpdateConfigRequest,
    app: str = "benefit-iq-be",
    env: str = "development",
    config_service: AppConfigService = Depends(Provide["app_config_service"]),
):
    """Admin Only: Updates an existing application configuration key and invalidates/updates Redis cache."""
    saved = await config_service.set_config(
        config_key=config_key,
        value=request.value,
        is_secret=request.is_secret,
        secret_path=request.secret_path,
        secret_key=request.secret_key,
        description=request.description,
        app=app,
        env=env,
    )
    return ApiResponse(
        success=True,
        data=AppConfigResponse(
            id=saved.id,
            application=saved.application,
            environment=saved.environment,
            config_key=saved.config_key,
            config_value=saved.config_value,
            is_secret=saved.is_secret,
            secret_path=saved.secret_path,
            secret_key=saved.secret_key,
            description=saved.description,
            is_active=saved.is_active,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        ),
    )


@router.delete("/{config_key}", response_model=ApiResponse[dict])
@inject
async def delete_config(
    config_key: str,
    app: str = "benefit-iq-be",
    env: str = "development",
    config_service: AppConfigService = Depends(Provide["app_config_service"]),
):
    """Admin Only: Deactivates configuration entry and invalidates Redis cache key."""
    success = await config_service.delete_config(config_key, app=app, env=env)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration key '{config_key}' not found or already deleted.",
        )
    return ApiResponse(
        success=True,
        data={"message": f"Configuration key '{config_key}' deleted successfully."},
    )
