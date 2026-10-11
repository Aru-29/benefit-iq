"""
Module missing docstring.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import (
    Resource,
)
from opentelemetry.sdk.trace import (
    TracerProvider,
)
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)

from benefit_iq.infrastructure.configuration.settings import (
    Settings,
)


def configure_tracing(
    settings: Settings,
) -> None:
    """Function missing docstring."""
    resource = Resource.create(
        {
            "service.name": (settings.telemetry.service_name),
            "service.version": (settings.app_version),
            "deployment.environment": (settings.app_env),
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=(settings.telemetry.exporter_otlp_endpoint),
        insecure=True,
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
