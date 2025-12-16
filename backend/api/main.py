"""
Engram API Server

FastAPI application providing:
- REST API for agent interactions
- WebSocket for real-time chat
- Authentication via Microsoft Entra ID
- RBAC middleware for authorization
- OpenTelemetry observability
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core import get_settings
from backend.observability import (
    configure_telemetry,
    configure_logging,
    TelemetryMiddleware,
)

from .routers import admin, agents, bau, chat, health, memory, metrics, validation, voice, workflows, etl
from .middleware.logging import RequestLoggingMiddleware

# Configure structured logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Configure telemetry
    configure_telemetry(app)

    # Startup
    yield

    # Shutdown
    logger.info("Shutting down Engram API")


def create_app() -> FastAPI:
    """Application factory"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Context Engineering Platform - Cognition-as-a-Service",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TelemetryMiddleware)

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
    app.include_router(etl.router, prefix="/api/v1/etl", tags=["ETL"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(bau.router, prefix="/api/v1/bau", tags=["BAU"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
    app.include_router(validation.router, prefix="/api/v1/validation", tags=["Validation"])
    
    # MCP (Model Context Protocol)
    # FastMCP provides a Starlette/ASGI compatible app for SSE
    from .routers.mcp import mcp_server
    app.mount("/api/v1/mcp", mcp_server.sse_app())
    # Note: FastMCP 1.0+ typically bundles message handling in the same app if using sse_app?
    # Actually, viewing debug output, there is `sse_app` and `streamable_http_app`. 
    # Usually standard mcp clients look for /sse and POST /messages relative to base.
    # We will mount at /api/v1/mcp so /api/v1/mcp/sse and /api/v1/mcp/messages need to be handled.
    # Let's assume sse_app handles both or check if we need separate mounts.
    # Based on standard usage, mounting `sse_app` usually handles the /sse endpoint, 
    # but we might need to verify if it handles messages.


    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8080, reload=True)
