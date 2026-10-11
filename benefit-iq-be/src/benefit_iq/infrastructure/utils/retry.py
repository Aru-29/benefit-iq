"""
Module missing docstring.
"""

import asyncio
import random
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


async def with_retry(
    operation: Callable[[], Any],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    operation_name: str = "operation",
) -> T:
    """
    Executes an async operation with bounded retries, exponential backoff, and jitter.
    """
    attempt = 1
    while True:
        try:
            return await operation()
        except retryable_exceptions as e:
            if attempt >= max_attempts:
                logger.error(
                    "operation_failed_max_retries",
                    operation=operation_name,
                    attempts=attempt,
                    error=str(e),
                )
                raise

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            jitter = random.uniform(0, delay * 0.1)
            sleep_time = delay + jitter

            logger.warning(
                "operation_failed_retrying",
                operation=operation_name,
                attempt=attempt,
                next_delay=round(sleep_time, 2),
                error=str(e),
            )

            await asyncio.sleep(sleep_time)
            attempt += 1
