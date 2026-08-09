"""Correlation ID Middleware for HTTP Request Tracing.

Extracts or generates X-Correlation-ID headers for request tracking across logs and spans.
"""
from uuid import uuid4

import structlog
from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request


CORRELATION_HEADER = "X-Correlation-ID"


# pylint: disable=too-few-public-methods
class CorrelationIdMiddleware(
    BaseHTTPMiddleware
):

    """Class missing docstring."""
    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        """Async function missing docstring."""
        correlation_id = (
            request.headers.get(
                CORRELATION_HEADER
            )
            or str(uuid4())
        )

        structlog.contextvars.clear_contextvars()

        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
        )

        response = await call_next(request)

        response.headers[
            CORRELATION_HEADER
        ] = correlation_id

        return response
