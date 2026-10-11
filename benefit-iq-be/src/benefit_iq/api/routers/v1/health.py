"""Liveness and fail-closed readiness probes."""

import asyncio

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def live():
    return {"status": "UP"}


@router.get("/ready")
@inject
async def ready(database=Depends(Provide["clickhouse"]), cache=Depends(Provide["redis"])):
    try:
        db_ok = await asyncio.to_thread(database.ping)
        cache_ok = cache.client is not None and await cache.client.ping()
    except Exception:
        db_ok = cache_ok = False
    return JSONResponse(
        status_code=200 if db_ok and cache_ok else 503,
        content={
            "status": "UP" if db_ok and cache_ok else "DOWN",
            "dependencies": {
                "clickhouse": "UP" if db_ok else "DOWN",
                "redis": "UP" if cache_ok else "DOWN",
            },
        },
    )
