"""Health check endpoints"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    Used by Kubernetes/Container Apps for routing traffic.
    """
    checks = {
        "api": True,
        "database": False,  # TODO: Implement actual check
        "zep": False,  # TODO: Implement actual check
        "temporal": False,  # TODO: Implement actual check
    }

    all_ready = all(checks.values())

    return ReadinessResponse(
        status="ready" if all_ready else "degraded",
        checks=checks,
    )
