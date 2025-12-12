import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Models ---


class SystemSettings(BaseModel):
    app_name: str
    maintenance_mode: bool
    default_agent: str
    theme: str
    log_level: str


class UserProfile(BaseModel):
    user_id: str
    email: str
    role: str
    active: bool
    last_login: Optional[str] = None


class AuditLog(BaseModel):
    id: str
    timestamp: str
    user_id: str
    action: str
    resource: str
    details: Optional[str] = None


# --- Mock Data Store ---

_current_settings = SystemSettings(
    app_name="Engram AI",
    maintenance_mode=False,
    default_agent="elena",
    theme="system",
    log_level="INFO",
)

_mock_users = [
    UserProfile(
        user_id="user-1",
        email="admin@engram.work",
        role="admin",
        active=True,
        last_login="2024-12-09T10:00:00Z",
    ),
    UserProfile(
        user_id="user-2",
        email="dev@engram.work",
        role="developer",
        active=True,
        last_login="2024-12-08T15:30:00Z",
    ),
]

_mock_audit_logs = [
    AuditLog(
        id="log-1",
        timestamp="2024-12-09T10:05:00Z",
        user_id="user-1",
        action="UPDATE",
        resource="settings",
        details="Changed theme to dark",
    ),
    AuditLog(
        id="log-2",
        timestamp="2024-12-09T09:00:00Z",
        user_id="system",
        action="STARTUP",
        resource="backend",
    ),
]

# --- Endpoints ---


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(user: SecurityContext = Depends(get_current_user)):
    """Get current system configuration."""
    return _current_settings


@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(settings: SystemSettings, user: SecurityContext = Depends(get_current_user)):
    """Update system configuration."""
    global _current_settings
    _current_settings = settings
    logger.info(f"System settings updated by {user.user_id}")
    return _current_settings


@router.get("/users", response_model=List[UserProfile])
async def list_users(user: SecurityContext = Depends(get_current_user)):
    """List registered users."""
    return _mock_users


@router.get("/audit", response_model=List[AuditLog])
async def get_audit_logs(user: SecurityContext = Depends(get_current_user)):
    """Get system audit logs."""
    return _mock_audit_logs
