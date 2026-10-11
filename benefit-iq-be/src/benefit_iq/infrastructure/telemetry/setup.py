"""Telemetry Configuration and Auto-instrumentation Setup."""

import structlog
from fastapi import FastAPI

from benefit_iq.infrastructure.configuration.settings import Settings
from benefit_iq.infrastructure.telemetry.metrics import configure_metrics
from benefit_iq.infrastructure.telemetry.tracing import configure_tracing

logger = structlog.get_logger(__name__)


def configure_telemetry(
    app: FastAPI,
    settings: Settings,
) -> None:
    """Configures tracing, metrics, and conditional auto-instrumentations."""
    if not settings.telemetry.enabled:
        return

    configure_tracing(settings)
    configure_metrics(settings)

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        logger.warning("telemetry_fastapi_instrumentation_failed", error=str(e))

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception as e:
        logger.warning("telemetry_httpx_instrumentation_failed", error=str(e))

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except Exception as e:
        logger.warning("telemetry_redis_instrumentation_failed", error=str(e))

    try:
        from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor

        ConfluentKafkaInstrumentor().instrument()
    except Exception as e:
        logger.warning("telemetry_kafka_instrumentation_failed", error=str(e))
