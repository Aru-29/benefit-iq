"""
Module missing docstring.
"""

import logging
import sys

import structlog

from benefit_iq.infrastructure.configuration.settings import (
    Settings,
)


def configure_logging(
    settings: Settings,
) -> None:
    """Function missing docstring."""
    timestamper = structlog.processors.TimeStamper(
        fmt="iso",
        utc=True,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_json:
        processors.append(structlog.processors.JSONRenderer())

    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=(structlog.stdlib.BoundLogger),
        logger_factory=(structlog.stdlib.LoggerFactory()),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level,
        force=True,
    )
