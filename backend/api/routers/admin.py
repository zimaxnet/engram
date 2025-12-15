import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext

logger = logging.getLogger(__name__)

router = APIRouter()

STATE_PATH = Path(__file__).resolve().parents[2] / "data" / "admin_state.json"

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


# --- Persistent Data Store (JSON-backed) ---


def _default_state() -> dict:
    return {
        "settings": SystemSettings(
            app_name="Engram AI",
            maintenance_mode=False,
            default_agent="elena",
            theme="system",
            log_level="INFO",
        ).model_dump(),
        "users": [
            UserProfile(
                user_id="user-1",
                email="admin@engram.work",
                role="admin",
                active=True,
                last_login="2025-01-05T10:00:00Z",
            ).model_dump(),
            UserProfile(
                user_id="user-2",
                email="dev@engram.work",
                role="developer",
                active=True,
                last_login="2025-01-04T15:30:00Z",
            ).model_dump(),
        ],
        "audit": [
            AuditLog(
                id="log-1",
                timestamp="2025-01-05T10:05:00Z",
                user_id="user-1",
                action="UPDATE",
                resource="settings",
                details="Initialized defaults",
            ).model_dump(),
        ],
    }


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            with STATE_PATH.open("r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            logger.exception("Failed to read admin state; using defaults")
    default_state = _default_state()
    _persist_state(default_state)
    return default_state


def _persist_state(state: dict) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with STATE_PATH.open("w", encoding="utf-8") as fp:
            json.dump(state, fp, indent=2)
    except Exception:
        logger.exception("Failed to persist admin state")


def _append_audit(state: dict, user_id: str, action: str, resource: str, details: Optional[str] = None) -> None:
    audit = state.setdefault("audit", [])
    entry = AuditLog(
        id=f"audit-{len(audit)+1}",
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
    ).model_dump()
    audit.insert(0, entry)


# --- Endpoints ---


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings(user: SecurityContext = Depends(get_current_user)):
    """Get current system configuration."""
    state = _load_state()
    settings = state.get("settings") or _default_state()["settings"]
    return SystemSettings(**settings)


@router.put("/settings", response_model=SystemSettings)
async def update_system_settings(settings: SystemSettings, user: SecurityContext = Depends(get_current_user)):
    """Update system configuration."""
    state = _load_state()
    state["settings"] = settings.model_dump()
    _append_audit(state, user.user_id, action="UPDATE", resource="settings", details="Updated system settings")
    _persist_state(state)
    logger.info(f"System settings updated by {user.user_id}")
    return settings


@router.get("/users", response_model=List[UserProfile])
async def list_users(user: SecurityContext = Depends(get_current_user)):
    """List registered users."""
    state = _load_state()
    users = state.get("users") or []
    return [UserProfile(**u) for u in users]


@router.get("/audit", response_model=List[AuditLog])
async def get_audit_logs(user: SecurityContext = Depends(get_current_user)):
    """Get system audit logs."""
    state = _load_state()
    logs = state.get("audit") or []
    return [AuditLog(**log) for log in logs]
