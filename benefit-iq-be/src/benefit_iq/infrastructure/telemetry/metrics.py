"""
Module missing docstring.
"""
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from benefit_iq.infrastructure.configuration.settings import (
    Settings,
)


def configure_metrics(
    settings: Settings,
) -> None:

    """Function missing docstring."""
    resource = Resource.create(
        {
            "service.name": (
                settings.telemetry.service_name
            ),
            "service.version": (
                settings.app_version
            ),
            "deployment.environment": (
                settings.app_env
            ),
        }
    )

    exporter = OTLPMetricExporter(
        endpoint=(
            settings.telemetry
            .exporter_otlp_endpoint
        ),
        insecure=True,
    )

    reader = PeriodicExportingMetricReader(exporter)

    provider = MeterProvider(
        resource=resource,
        metric_readers=[reader],
    )

    metrics.set_meter_provider(provider)
