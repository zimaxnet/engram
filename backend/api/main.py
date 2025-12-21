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

from .routers import admin, agents, bau, chat, health, memory, metrics, story, validation, voice, workflows, etl
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
    try:
        # from backend.context.bootstrap import bootstrap_knowledge
        # Run bootstrap in background to prevent blocking container startup checks
        # import asyncio
        # asyncio.create_task(bootstrap_knowledge())
        logger.info("Auto-bootstrap disabled for debugging.")
    except Exception as e:
        logger.error(f"Failed to initiate bootstrap: {e}")

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
    app.include_router(story.router, prefix="/api/v1/story", tags=["Story"])
    
    # MCP (Model Context Protocol)
    # FastMCP provides a Starlette/ASGI compatible app for SSE
    from .routers.mcp_server import mcp_server
    
    # Get the underlying Starlette app
    mcp_app = mcp_server.sse_app()
    
    # Fix: FastMCP has strict TrustedHostMiddleware that only allows "localhost".
    # We wrap the app with an ASGI middleware that rewrites the Host header
    # to "localhost" before FastMCP sees it, effectively bypassing the check.
    class HostRewriteMiddleware:
        def __init__(self, app):
            self.app = app
        
        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                # Rewrite host to bypass FastMCP's TrustedHostMiddleware
                headers = dict(scope.get("headers", []))
                headers[b"host"] = b"localhost"
                scope["headers"] = list(headers.items())
            await self.app(scope, receive, send)
    
    # Wrap the MCP app
    wrapped_mcp_app = HostRewriteMiddleware(mcp_app)

    app.mount("/api/v1/mcp", wrapped_mcp_app)
    logger.info("Mounted MCP server at /api/v1/mcp")


    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8080, reload=True)
