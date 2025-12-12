"""
Structured Logging Configuration

Provides:
- JSON-formatted logs for production
- Correlation with traces
- User context injection
- Azure Log Analytics integration
"""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from opentelemetry import trace

from backend.core import get_settings


class JsonFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Output format:
    {
        "timestamp": "2024-01-01T00:00:00.000Z",
        "level": "INFO",
        "message": "...",
        "logger": "...",
        "trace_id": "...",
        "span_id": "...",
        "user_id": "...",
        "tenant_id": "...",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add trace context
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            log_data["trace_id"] = format(ctx.trace_id, "032x")
            log_data["span_id"] = format(ctx.span_id, "016x")

        # Add user context if available
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        extra = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "user_id",
                "tenant_id",
                "session_id",
                "message",
            }:
                extra[key] = value

        if extra:
            log_data["extra"] = extra

        return json.dumps(log_data, default=str)


class PrettyFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")

        # Build prefix
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = f"{color}{timestamp} [{record.levelname:8}]{self.RESET}"

        # Add trace context
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, "032x")[-8:]
            prefix += f" [{trace_id}]"

        # Build message
        message = record.getMessage()

        # Add location for errors
        if record.levelno >= logging.WARNING:
            message += f" ({record.module}:{record.lineno})"

        # Add exception
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)

        return f"{prefix} {message}"


class StructuredLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds context to all log messages.

    Usage:
        logger = StructuredLogger(logging.getLogger(__name__))
        logger.bind(user_id="user123", tenant_id="tenant456")
        logger.info("Processing request")
    """

    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        super().__init__(logger, extra or {})
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs) -> "StructuredLogger":
        """Add context that will be included in all subsequent logs"""
        self._context.update(kwargs)
        return self

    def unbind(self, *keys) -> "StructuredLogger":
        """Remove context keys"""
        for key in keys:
            self._context.pop(key, None)
        return self

    def process(self, msg, kwargs):
        # Merge extra context
        extra = kwargs.get("extra", {})
        extra.update(self._context)
        kwargs["extra"] = extra
        return msg, kwargs

    def with_context(self, **kwargs) -> "StructuredLogger":
        """Create a new logger with additional context"""
        new_logger = StructuredLogger(self.logger, self.extra)
        new_logger._context = {**self._context, **kwargs}
        return new_logger


def configure_logging() -> None:
    """
    Configure logging for the application.

    Uses JSON format in production, pretty format in development.
    """
    settings = get_settings()

    # Determine log level
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Create root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use appropriate formatter
    if settings.environment == "production":
        formatter = JsonFormatter()
    else:
        formatter = PrettyFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)

    # Log configuration
    root_logger.info(
        f"Logging configured: level={logging.getLevelName(log_level)}, "
        f"format={'json' if settings.environment == 'production' else 'pretty'}"
    )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger for a module.

    Usage:
        logger = get_logger(__name__)
        logger.info("Starting process", extra={"step": 1})
    """
    return StructuredLogger(logging.getLogger(name))


# Context variable for request-scoped logging
_log_context: contextvars.ContextVar[dict] = contextvars.ContextVar("log_context", default={})


def set_log_context(**kwargs) -> None:
    """Set logging context for the current request"""
    ctx = _log_context.get()
    _log_context.set({**ctx, **kwargs})


def get_log_context() -> dict:
    """Get current logging context"""
    return _log_context.get()


def clear_log_context() -> None:
    """Clear logging context"""
    _log_context.set({})
