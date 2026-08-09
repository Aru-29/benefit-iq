"""
ClickHouse database connection and query execution utilities.
"""
from typing import Any
import asyncio

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError

from benefit_iq.infrastructure.configuration.settings import (
    ClickHouseSettings,
)
from benefit_iq.infrastructure.utils.retry import with_retry


class ClickHouseDatabase:
    """
    Manages connections and query execution for ClickHouse.
    """

    def __init__(
        self,
        settings: ClickHouseSettings,
    ) -> None:
        """Initialize the ClickHouse database connection manager."""
        self._settings = settings
        self._client: Any | None = None

    def connect(self) -> None:
        """Establish a connection to the ClickHouse database."""
        if self._client is not None:
            return

        self._client = clickhouse_connect.get_client(
            host=self._settings.host,
            port=self._settings.port,
            username=self._settings.username,
            password=self._settings.password,
            database=self._settings.database,
            secure=self._settings.secure,
            connect_timeout=self._settings.connect_timeout,
            send_receive_timeout=(
                self._settings.send_receive_timeout
            ),
        )

    @property
    def client(self) -> Any:
        """Return the active ClickHouse client instance."""
        if self._client is None:
            raise RuntimeError(
                "ClickHouse client is not initialized."
            )

        return self._client

    def ping(self) -> bool:
        """Ping the ClickHouse database to verify connectivity."""
        try:
            self.client.command("SELECT 1")
            return True
        except ClickHouseError:
            return False

    async def execute_async(self, query: str, parameters: dict | list | None = None) -> None:
        """Execute a DML or DDL query asynchronously using a thread pool."""
        loop = asyncio.get_running_loop()

        async def do_execute() -> None:
            await loop.run_in_executor(
                None,
                lambda: self.client.command(query, parameters=parameters)
            )

        await with_retry(
            operation=do_execute,
            retryable_exceptions=(ClickHouseError,),
            operation_name="clickhouse_execute"
        )

    async def query_async(self, query: str, parameters: dict | list | None = None) -> Any:
        """Execute a SELECT query asynchronously and return the result."""
        loop = asyncio.get_running_loop()

        async def do_query() -> Any:
            return await loop.run_in_executor(
                None,
                lambda: self.client.query(query, parameters=parameters)
            )

        return await with_retry(
            operation=do_query,
            retryable_exceptions=(ClickHouseError,),
            operation_name="clickhouse_query"
        )

    def close(self) -> None:
        """Close the active ClickHouse connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
