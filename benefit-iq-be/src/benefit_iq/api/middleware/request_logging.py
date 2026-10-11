"""Structured HTTP Request Logging Middleware."""

import time

import structlog
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request

logger = structlog.get_logger(__name__)


# pylint: disable=too-few-public-methods
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Class missing docstring."""

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        """Async function missing docstring."""
        start = time.perf_counter()

        try:
            response = await call_next(request)

            duration_ms = (time.perf_counter() - start) * 1000

            logger.info(
                "http_request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(
                    duration_ms,
                    2,
                ),
            )

            return response

        except Exception:  # pylint: disable=broad-exception-caught
            duration_ms = (time.perf_counter() - start) * 1000

            logger.exception(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(
                    duration_ms,
                    2,
                ),
            )

            raise
