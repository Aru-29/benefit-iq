"""OpenBao Vault Secrets Management Proxy API Router.

Provides administrative REST endpoints for listing, storing, reading, and rotating
secrets securely stored inside OpenBao Vault without exposing OpenBao directly to FE.
"""
from typing import Any
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from benefit_iq.api.dependencies.auth import get_current_admin_user
from benefit_iq.api.schemas.common import ApiResponse
from benefit_iq.infrastructure.secrets.openbao_manager import OpenBaoSecretsManager

router = APIRouter(
    prefix="/secrets",
    tags=["OpenBao Secret Management"],
    dependencies=[Depends(get_current_admin_user)],
)


class SecretWriteRequest(BaseModel):
    """Payload for writing or updating a secret in OpenBao."""

    path: str
    key: str
    value: str


@router.get("", response_model=ApiResponse[list[dict[str, Any]]])
@inject
async def list_secret_metadata(
    secrets_manager: OpenBaoSecretsManager = Depends(Provide["openbao_manager"]),
):
    """Admin Only: Lists authorized system secret paths and metadata status."""
    managed_paths = [
        {"path": "secret/data/benefit-iq-be/jwt_secret_key", "key": "secret_value", "description": "JWT Signing Key"},
        {"path": "secret/data/benefit-iq-be/smtp_password", "key": "secret_value", "description": "SMTP Email Password"},
        {"path": "secret/data/benefit-iq-be/database_credentials", "key": "db_pass", "description": "ClickHouse DB Credentials"},
        {"path": "secret/data/benefit-iq-be/redis_auth_token", "key": "token", "description": "Redis Cache Token"},
    ]
    results = []
    for item in managed_paths:
        val = await secrets_manager.get_secret(item["path"], item["key"])
        results.append({
            "path": item["path"],
            "key": item["key"],
            "description": item["description"],
            "is_configured": bool(val),
            "masked_value": "••••••••••••" if val else "NOT_SET",
        })
    return ApiResponse(success=True, data=results)


@router.post("/value", response_model=ApiResponse[dict[str, Any]])
@inject
async def set_secret_value(
    request: SecretWriteRequest,
    secrets_manager: OpenBaoSecretsManager = Depends(Provide["openbao_manager"]),
):
    """Admin Only: Writes a secret key-value pair to OpenBao Vault."""
    try:
        await secrets_manager.set_secret(path=request.path, secrets={request.key: request.value})
        return ApiResponse(
            success=True,
            data={"message": f"Secret '{request.key}' at '{request.path}' successfully stored in OpenBao."},
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set secret in OpenBao: {str(e)}",
        ) from e


@router.post("/rotate", response_model=ApiResponse[dict[str, Any]])
@inject
async def rotate_secret_key(
    request: SecretWriteRequest,
    secrets_manager: OpenBaoSecretsManager = Depends(Provide["openbao_manager"]),
):
    """Admin Only: Rotates a secret key in OpenBao Vault."""
    await secrets_manager.set_secret(path=request.path, secrets={request.key: request.value})
    return ApiResponse(
        success=True,
        data={"message": f"Secret '{request.key}' at path '{request.path}' rotated successfully."},
    )
