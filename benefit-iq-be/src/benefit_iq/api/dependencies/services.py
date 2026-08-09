"""Dependency Injection service providers for API endpoints."""
from typing import Any

from dependency_injector.wiring import (
    Provide,
    inject,
)

from benefit_iq.infrastructure.persistence.clickhouse.database import (
    ClickHouseDatabase,
)


@inject
def get_clickhouse_database(
    database: Any = Provide["clickhouse"],
) -> ClickHouseDatabase:

    """Function missing docstring."""
    return database
