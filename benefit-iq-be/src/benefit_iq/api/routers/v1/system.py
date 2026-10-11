"""Read-only administrative runtime diagnostics."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from benefit_iq.api.dependencies.auth import get_current_admin_user
from benefit_iq.api.schemas.common import ApiResponse

router = APIRouter(
    prefix="/system", tags=["Runtime diagnostics"], dependencies=[Depends(get_current_admin_user)]
)


@router.get("/redis/stats")
@inject
async def redis_stats(cache=Depends(Provide["redis"])):
    if cache.client is None:
        raise HTTPException(503, "Redis is unavailable")
    info = await cache.client.info()
    return ApiResponse(
        success=True,
        data={
            key: info.get(key)
            for key in (
                "connected_clients",
                "used_memory_human",
                "uptime_in_seconds",
                "keyspace_hits",
                "keyspace_misses",
            )
        },
    )
