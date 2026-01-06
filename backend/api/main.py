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

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from backend.core import get_settings

# Defensive Observability Import
try:
    from backend.observability import (
        configure_telemetry,
        configure_logging,
        TelemetryMiddleware,
    )
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    # Fallback logger configuration if observability module is missing
    logging.basicConfig(level=logging.INFO)
    def configure_logging(): pass
    def configure_telemetry(app): pass
    TelemetryMiddleware = None
    OBSERVABILITY_AVAILABLE = False

from .routers import admin, agents, bau, chat, health, memory, metrics, story, validation, voice, workflows, etl, images, graph, tools
from .middleware.logging import RequestLoggingMiddleware
from .middleware.cors_preflight import CORSPreflightMiddleware

# Configure structured logging (if available)
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Configure telemetry (if available)
    if OBSERVABILITY_AVAILABLE:
        configure_telemetry(app)
    else:
        logger.warning("Observability module missing; telemetry disabled.")

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

    # CORS middleware (handles preflight OPTIONS requests automatically)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers to ensure CORS headers are added to error responses
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Ensure CORS headers are added to HTTPException responses"""
        origin = request.headers.get("origin")
        allowed_origins = settings.cors_origins
        is_allowed = origin and (origin in allowed_origins or "*" in allowed_origins)
        
        headers = dict(exc.headers) if exc.headers else {}
        
        # Add CORS headers
        if is_allowed and origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        elif "*" in allowed_origins:
            headers["Access-Control-Allow-Origin"] = "*"
        
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        headers["Access-Control-Allow-Headers"] = "authorization, content-type"
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Ensure CORS headers are added to validation error responses"""
        origin = request.headers.get("origin")
        allowed_origins = settings.cors_origins
        is_allowed = origin and (origin in allowed_origins or "*" in allowed_origins)
        
        headers = {}
        
        # Add CORS headers
        if is_allowed and origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        elif "*" in allowed_origins:
            headers["Access-Control-Allow-Origin"] = "*"
        
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        headers["Access-Control-Allow-Headers"] = "authorization, content-type"
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
            headers=headers,
        )

    # Custom middleware
    # NOTE: Middleware runs in REVERSE order from how they're added.
    app.add_middleware(RequestLoggingMiddleware)
    
    if OBSERVABILITY_AVAILABLE and TelemetryMiddleware:
        app.add_middleware(TelemetryMiddleware)
        
    # Trust the Azure Container Apps load balancer to handle SSL/Host headers correctly
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])
    app.add_middleware(CORSPreflightMiddleware)

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
    app.include_router(images.router, prefix="/api/v1/images", tags=["Images"])
    app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
    app.include_router(tools.router, prefix="/api/v1", tags=["Tools"])  # Tool endpoints for Foundry agents
    
    # MCP (Model Context Protocol) - Defensive Loading
    try:
        from .routers.mcp_server import mcp_server
        
        # Get the underlying Starlette app
        mcp_app = mcp_server.sse_app()
        
        # Wrapped app to fix Host header issues in FastMCP
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
        
        wrapped_mcp_app = HostRewriteMiddleware(mcp_app)
        app.mount("/api/v1/mcp", wrapped_mcp_app)
        logger.info("Mounted MCP server at /api/v1/mcp")
        
    except ImportError as e:
        logger.warning(f"MCP Server components missing (FastMCP/SSE). MCP endpoint disabled: {e}")
    except Exception as e:
        logger.error(f"Failed to mount MCP server: {e}")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    # If running directly, we can't easily patch observability imports at module level
    # so we rely on what was loaded above.
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8080, reload=True)
