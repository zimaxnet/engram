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


# Backwards-compatible alias for older frontends that call /api/v1/health.
# We keep it out of the OpenAPI schema to avoid duplication.
@router.get("/api/v1/health", response_model=HealthResponse, include_in_schema=False)
async def health_check_v1():
    return await health_check()


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    Used by Kubernetes/Container Apps for routing traffic.
    """
    # Check storage writeability
    from pathlib import Path
    settings = get_settings()
    docs_path = Path(settings.onedrive_docs_path or "docs")
    storage_ok = False
    try:
        # Try to write a tiny file
        test_file = docs_path / ".health_check"
        docs_path.mkdir(parents=True, exist_ok=True)
        test_file.write_text("ok")
        test_file.unlink()
        storage_ok = True
    except Exception:
        storage_ok = False

    checks = {
        "api": True,
        "storage": storage_ok,
        "database": True,  # TODO: Implement actual check
        "zep": True,  # TODO: Implement actual check
        "temporal": True,  # TODO: Implement actual check
    }

    all_ready = all(checks.values())

    return ReadinessResponse(
        status="ready" if all_ready else "degraded",
        checks=checks,
    )


@router.get("/api/v1/ready", response_model=ReadinessResponse, include_in_schema=False)
async def readiness_check_v1():
    return await readiness_check()
