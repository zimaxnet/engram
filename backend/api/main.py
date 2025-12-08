"""
Engram API Server

FastAPI application providing:
- REST API for agent interactions
- WebSocket for real-time chat
- Authentication via Microsoft Entra ID
- RBAC middleware for authorization
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core import get_settings

from .routers import agents, chat, health, memory, workflows
from .middleware.logging import RequestLoggingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
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
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8080, reload=True)

