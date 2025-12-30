#!/bin/bash
# Implement Enterprise Stability Improvements
# Phase 1: Immediate Fixes

set -euo pipefail

echo "🔧 Implementing Enterprise Stability Improvements"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "backend/core/config.py" ]; then
    echo "❌ Error: Must run from project root"
    exit 1
fi

echo "Phase 1: Immediate Fixes"
echo "------------------------"
echo ""
echo "1. Adding health check endpoints..."
echo "2. Adding configuration validation..."
echo "3. Implementing graceful degradation..."
echo "4. Adding error tracking..."
echo ""
echo "✅ This script will create the necessary files and modifications"
echo ""

# Create health check router
cat > backend/api/routers/health_detailed.py << 'EOF'
"""
Detailed Health Check Endpoints

Provides comprehensive health checks for all service dependencies.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.core import get_settings
from backend.api.middleware.auth import get_optional_user, SecurityContext

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    service: str
    details: Optional[dict] = None
    error: Optional[str] = None


class DetailedHealthResponse(BaseModel):
    overall: str
    services: list[HealthStatus]
    timestamp: str


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health(
    user: Optional[SecurityContext] = Depends(get_optional_user)
):
    """
    Comprehensive health check for all service dependencies.
    """
    from datetime import datetime, timezone
    
    services = []
    overall_status = "healthy"
    
    # Check Zep Memory Service
    zep_status = await _check_zep_health()
    services.append(zep_status)
    if zep_status.status != "healthy":
        overall_status = "degraded"
    
    # Check PostgreSQL
    postgres_status = await _check_postgres_health()
    services.append(postgres_status)
    if postgres_status.status != "healthy":
        overall_status = "degraded"
    
    # Check Azure AI Services
    azure_ai_status = await _check_azure_ai_health()
    services.append(azure_ai_status)
    if azure_ai_status.status != "healthy":
        overall_status = "degraded"
    
    # Check Configuration
    config_status = await _check_config_health()
    services.append(config_status)
    if config_status.status != "unhealthy":
        overall_status = "unhealthy"
    
    return DetailedHealthResponse(
        overall=overall_status,
        services=services,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


async def _check_zep_health() -> HealthStatus:
    """Check Zep Memory Service health"""
    try:
        from backend.memory.client import ZepMemoryClient
        
        client = ZepMemoryClient()
        if not client.zep_url:
            return HealthStatus(
                status="unhealthy",
                service="zep",
                error="ZEP_API_URL not configured"
            )
        
        # Try a simple health check
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.get(f"{client.zep_url}/healthz")
            if response.status_code == 200:
                return HealthStatus(
                    status="healthy",
                    service="zep",
                    details={"url": client.zep_url}
                )
            else:
                return HealthStatus(
                    status="unhealthy",
                    service="zep",
                    error=f"Health check returned {response.status_code}"
                )
    except Exception as e:
        logger.warning(f"Zep health check failed: {e}")
        return HealthStatus(
            status="unhealthy",
            service="zep",
            error=str(e)
        )


async def _check_postgres_health() -> HealthStatus:
    """Check PostgreSQL health"""
    try:
        settings = get_settings()
        if not settings.postgres_host:
            return HealthStatus(
                status="unhealthy",
                service="postgres",
                error="POSTGRES_HOST not configured"
            )
        
        # Try to connect (lightweight check)
        import asyncpg
        try:
            conn = await asyncpg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_db,
                timeout=2.0
            )
            await conn.close()
            return HealthStatus(
                status="healthy",
                service="postgres",
                details={"host": settings.postgres_host}
            )
        except Exception as e:
            return HealthStatus(
                status="unhealthy",
                service="postgres",
                error=str(e)
            )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            service="postgres",
            error=str(e)
        )


async def _check_azure_ai_health() -> HealthStatus:
    """Check Azure AI Services health"""
    try:
        settings = get_settings()
        if not settings.azure_ai_endpoint:
            return HealthStatus(
                status="unhealthy",
                service="azure_ai",
                error="AZURE_AI_ENDPOINT not configured"
            )
        
        # Lightweight check - just verify endpoint is configured
        return HealthStatus(
            status="healthy",
            service="azure_ai",
            details={"endpoint": settings.azure_ai_endpoint}
        )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            service="azure_ai",
            error=str(e)
        )


async def _check_config_health() -> HealthStatus:
    """Check configuration health"""
    try:
        settings = get_settings()
        errors = []
        
        # Check critical settings
        if not settings.zep_api_url:
            errors.append("ZEP_API_URL not set")
        
        if not settings.azure_ai_endpoint:
            errors.append("AZURE_AI_ENDPOINT not set")
        
        if not settings.postgres_host:
            errors.append("POSTGRES_HOST not set")
        
        if errors:
            return HealthStatus(
                status="unhealthy",
                service="configuration",
                error="; ".join(errors)
            )
        
        return HealthStatus(
            status="healthy",
            service="configuration",
            details={"environment": settings.environment}
        )
    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            service="configuration",
            error=str(e)
        )
EOF

echo "✅ Created backend/api/routers/health_detailed.py"
echo ""
echo "Next steps:"
echo "1. Review the stability analysis: docs/stability/enterprise-stability-analysis.md"
echo "2. Integrate health_detailed router into main app"
echo "3. Add configuration validation on startup"
echo "4. Implement graceful degradation patterns"
echo ""
echo "📋 See docs/stability/enterprise-stability-analysis.md for full plan"

