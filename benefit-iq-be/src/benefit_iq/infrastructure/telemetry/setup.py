"""
Module missing docstring.
"""
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from opentelemetry.instrumentation.httpx import (
    HTTPXClientInstrumentor,
)
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor

from benefit_iq.infrastructure.configuration.settings import (
    Settings,
)
from benefit_iq.infrastructure.telemetry.metrics import (
    configure_metrics,
)
from benefit_iq.infrastructure.telemetry.tracing import (
    configure_tracing,
)


def configure_telemetry(
    app: FastAPI,
    settings: Settings,
) -> None:

    """Function missing docstring."""
    if not settings.telemetry.enabled:
        return

    configure_tracing(settings)
    configure_metrics(settings)

    FastAPIInstrumentor.instrument_app(app)

    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()
    ConfluentKafkaInstrumentor().instrument()
