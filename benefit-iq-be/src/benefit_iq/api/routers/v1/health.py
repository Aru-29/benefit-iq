"""Health & Diagnostics Router.

Provides operational readiness, liveness probes, and datastore health diagnostics.
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from benefit_iq.api.dependencies.services import (
    get_clickhouse_database,
)
from benefit_iq.infrastructure.persistence.clickhouse.database import (
    ClickHouseDatabase,
)


router = APIRouter(
    prefix="/health",
    tags=["Health & Diagnostics"],
)


@router.get("/live")
async def liveness():

    """Async function missing docstring."""
    return {
        "status": "UP",
    }


@router.get("/ready")
async def readiness(
    database: Annotated[
        ClickHouseDatabase,
        Depends(get_clickhouse_database),
    ],
):

    """Async function missing docstring."""
    clickhouse_status = database.ping()

    return {
        "status": (
            "UP"
            if clickhouse_status
            else "DOWN"
        ),
        "dependencies": {
            "clickhouse": (
                "UP"
                if clickhouse_status
                else "DOWN"
            ),
        },
    }
