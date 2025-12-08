"""
Engram Observability Module

OpenTelemetry integration for:
- Distributed tracing
- Metrics collection
- Log correlation
- Azure Application Insights export
"""

from .telemetry import (
    configure_telemetry,
    get_tracer,
    get_meter,
    create_span,
    record_metric,
    TelemetryMiddleware,
)

from .logging import (
    configure_logging,
    get_logger,
    StructuredLogger,
)

__all__ = [
    # Telemetry
    "configure_telemetry",
    "get_tracer",
    "get_meter",
    "create_span",
    "record_metric",
    "TelemetryMiddleware",
    # Logging
    "configure_logging",
    "get_logger",
    "StructuredLogger",
]

