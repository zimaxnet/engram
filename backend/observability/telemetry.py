"""
OpenTelemetry Integration

Provides distributed tracing and metrics for:
- API requests
- Agent executions
- Memory operations
- Workflow steps
"""

import asyncio
import logging
import os
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core import get_settings

logger = logging.getLogger(__name__)

# Global providers
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None


def configure_telemetry(app=None) -> None:
    """
    Configure OpenTelemetry for the application.

    Sets up:
    - TracerProvider with Azure Monitor exporter
    - MeterProvider for metrics
    - Automatic instrumentation for FastAPI and httpx
    """
    global _tracer_provider, _meter_provider

    settings = get_settings()

    # Create resource with service info
    resource = Resource.create(
        {
            "service.name": settings.app_name,
            "service.version": settings.app_version,
            "service.environment": settings.environment,
            "service.instance.id": os.environ.get("HOSTNAME", "local"),
        }
    )

    # Configure tracer
    _tracer_provider = TracerProvider(resource=resource)

    # Add Azure Monitor exporter if connection string is available
    if settings.appinsights_connection_string:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            azure_exporter = AzureMonitorTraceExporter(connection_string=settings.appinsights_connection_string)
            _tracer_provider.add_span_processor(BatchSpanProcessor(azure_exporter))
            logger.info("Azure Monitor trace exporter configured")
        except ImportError:
            logger.warning("Azure Monitor exporter not available")

    # Add OTLP exporter for local development (e.g., Jaeger)
    otlp_endpoint = os.environ.get("OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP trace exporter configured: {otlp_endpoint}")

    trace.set_tracer_provider(_tracer_provider)

    # Configure meter
    metric_readers = []

    if settings.appinsights_connection_string:
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorMetricExporter

            azure_metric_exporter = AzureMonitorMetricExporter(connection_string=settings.appinsights_connection_string)
            metric_readers.append(PeriodicExportingMetricReader(azure_metric_exporter))
        except ImportError:
            pass

    if otlp_endpoint:
        otlp_metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
        metric_readers.append(PeriodicExportingMetricReader(otlp_metric_exporter))

    if metric_readers:
        _meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
        metrics.set_meter_provider(_meter_provider)

    # Instrument FastAPI
    if app:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation enabled")

    # Instrument httpx
    HTTPXClientInstrumentor().instrument()

    logger.info("OpenTelemetry configured")


def get_tracer(name: str = "engram") -> trace.Tracer:
    """Get a tracer instance"""
    return trace.get_tracer(name)


def get_meter(name: str = "engram") -> metrics.Meter:
    """Get a meter instance"""
    return metrics.get_meter(name)


@contextmanager
def create_span(
    name: str,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Context manager to create a span.

    Usage:
        with create_span("process_message", {"user_id": user_id}):
            # Do work
            pass
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(name, kind=kind, attributes=attributes or {}) as span:
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def trace_function(name: Optional[str] = None, attributes: Optional[dict] = None) -> Callable:
    """
    Decorator to trace a function.

    Usage:
        @trace_function("process_message")
        async def process_message(user_id: str, message: str):
            pass
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with create_span(span_name, attributes):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with create_span(span_name, attributes):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def record_metric(name: str, value: float, attributes: Optional[dict] = None, unit: str = "") -> None:
    """
    Record a metric value.

    Usage:
        record_metric("tokens_used", 150, {"agent": "elena"})
    """
    meter = get_meter()
    counter = meter.create_counter(name, unit=unit, description=f"Counter for {name}")
    counter.add(value, attributes or {})


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add telemetry to requests.

    Adds:
    - Request/response timing
    - User context to spans
    - Error tracking
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract trace context from headers if present
        # (handled automatically by OpenTelemetry instrumentation)

        # Get current span
        span = trace.get_current_span()

        # Add request attributes
        if span.is_recording():
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))

            # Add user info if available
            user_id = request.headers.get("X-User-ID")
            if user_id:
                span.set_attribute("user.id", user_id)

            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                span.set_attribute("tenant.id", tenant_id)

        try:
            response = await call_next(request)

            if span.is_recording():
                span.set_attribute("http.status_code", response.status_code)

                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))

            return response

        except Exception as e:
            if span.is_recording():
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            raise


# Pre-defined metrics
def create_standard_metrics():
    """Create standard application metrics"""
    meter = get_meter()

    # Request metrics
    request_counter = meter.create_counter("http_requests_total", unit="1", description="Total HTTP requests")

    request_duration = meter.create_histogram(
        "http_request_duration_seconds", unit="s", description="HTTP request duration"
    )

    # Agent metrics
    agent_execution_counter = meter.create_counter(
        "agent_executions_total", unit="1", description="Total agent executions"
    )

    agent_tokens_counter = meter.create_counter(
        "agent_tokens_total", unit="1", description="Total tokens used by agents"
    )

    agent_execution_duration = meter.create_histogram(
        "agent_execution_duration_seconds",
        unit="s",
        description="Agent execution duration",
    )

    # Memory metrics
    memory_operations_counter = meter.create_counter(
        "memory_operations_total", unit="1", description="Total memory operations"
    )

    memory_search_duration = meter.create_histogram(
        "memory_search_duration_seconds", unit="s", description="Memory search duration"
    )

    # Workflow metrics
    workflow_executions_counter = meter.create_counter(
        "workflow_executions_total", unit="1", description="Total workflow executions"
    )

    workflow_duration = meter.create_histogram(
        "workflow_duration_seconds", unit="s", description="Workflow execution duration"
    )

    return {
        "request_counter": request_counter,
        "request_duration": request_duration,
        "agent_execution_counter": agent_execution_counter,
        "agent_tokens_counter": agent_tokens_counter,
        "agent_execution_duration": agent_execution_duration,
        "memory_operations_counter": memory_operations_counter,
        "memory_search_duration": memory_search_duration,
        "workflow_executions_counter": workflow_executions_counter,
        "workflow_duration": workflow_duration,
    }
