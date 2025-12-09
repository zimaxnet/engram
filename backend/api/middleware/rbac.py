"""
Role-Based Access Control (RBAC) Middleware

Provides fine-grained access control:
- Resource-level permissions
- Action-based authorization
- Tenant isolation
- Audit logging
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from backend.core import Role, SecurityContext
from .auth import get_current_user

logger = logging.getLogger(__name__)


class Action(str, Enum):
    """Available actions on resources"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class Resource(str, Enum):
    """Available resources"""

    AGENTS = "agents"
    CHAT = "chat"
    MEMORY = "memory"
    WORKFLOWS = "workflows"
    VOICE = "voice"
    USERS = "users"
    SETTINGS = "settings"
    AUDIT = "audit"


# Permission matrix: Role -> Resource -> Actions
PERMISSION_MATRIX: dict[Role, dict[Resource, set[Action]]] = {
    Role.ADMIN: {
        Resource.AGENTS: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.EXECUTE,
            Action.ADMIN,
        },
        Resource.CHAT: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.EXECUTE,
            Action.ADMIN,
        },
        Resource.MEMORY: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.ADMIN,
        },
        Resource.WORKFLOWS: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.EXECUTE,
            Action.ADMIN,
        },
        Resource.VOICE: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.EXECUTE,
        },
        Resource.USERS: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.ADMIN,
        },
        Resource.SETTINGS: {
            Action.CREATE,
            Action.READ,
            Action.UPDATE,
            Action.DELETE,
            Action.ADMIN,
        },
        Resource.AUDIT: {Action.READ},
    },
    Role.PM: {
        Resource.AGENTS: {Action.READ, Action.EXECUTE},
        Resource.CHAT: {Action.CREATE, Action.READ, Action.EXECUTE},
        Resource.MEMORY: {Action.CREATE, Action.READ},
        Resource.WORKFLOWS: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXECUTE},
        Resource.VOICE: {Action.CREATE, Action.READ, Action.EXECUTE},
        Resource.USERS: {Action.READ},
        Resource.SETTINGS: {Action.READ},
        Resource.AUDIT: {Action.READ},
    },
    Role.ANALYST: {
        Resource.AGENTS: {Action.READ, Action.EXECUTE},
        Resource.CHAT: {Action.CREATE, Action.READ, Action.EXECUTE},
        Resource.MEMORY: {Action.CREATE, Action.READ},
        Resource.WORKFLOWS: {Action.READ, Action.EXECUTE},
        Resource.VOICE: {Action.CREATE, Action.READ, Action.EXECUTE},
        Resource.USERS: set(),
        Resource.SETTINGS: {Action.READ},
        Resource.AUDIT: set(),
    },
    Role.VIEWER: {
        Resource.AGENTS: {Action.READ},
        Resource.CHAT: {Action.READ},
        Resource.MEMORY: {Action.READ},
        Resource.WORKFLOWS: {Action.READ},
        Resource.VOICE: {Action.READ},
        Resource.USERS: set(),
        Resource.SETTINGS: set(),
        Resource.AUDIT: set(),
    },
}


class PermissionDenied(HTTPException):
    """Exception raised when permission is denied"""

    def __init__(
        self, resource: Resource, action: Action, detail: Optional[str] = None
    ):
        message = detail or f"Permission denied: {action.value} on {resource.value}"
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)


class AuditLogEntry(BaseModel):
    """Audit log entry for access control events"""

    timestamp: datetime
    user_id: str
    tenant_id: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None


class RBACService:
    """
    RBAC service for checking permissions.
    """

    def __init__(self):
        self._audit_log: list[AuditLogEntry] = []

    def has_permission(
        self, user: SecurityContext, resource: Resource, action: Action
    ) -> bool:
        """
        Check if user has permission for action on resource.

        Args:
            user: The security context
            resource: The resource being accessed
            action: The action being performed

        Returns:
            True if permitted, False otherwise
        """
        for role in user.roles:
            permissions = PERMISSION_MATRIX.get(role, {})
            allowed_actions = permissions.get(resource, set())
            if action in allowed_actions:
                return True

        return False

    def check_permission(
        self,
        user: SecurityContext,
        resource: Resource,
        action: Action,
        resource_id: Optional[str] = None,
    ) -> None:
        """
        Check permission and raise exception if denied.

        Also logs the access attempt.
        """
        allowed = self.has_permission(user, resource, action)

        # Log the access attempt
        self.log_access(
            user=user,
            resource=resource,
            action=action,
            resource_id=resource_id,
            success=allowed,
        )

        if not allowed:
            raise PermissionDenied(resource, action)

    def log_access(
        self,
        user: SecurityContext,
        resource: Resource,
        action: Action,
        resource_id: Optional[str] = None,
        success: bool = True,
        details: Optional[dict] = None,
    ) -> None:
        """Log an access attempt"""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            action=action.value,
            resource=resource.value,
            resource_id=resource_id,
            success=success,
            details=details,
        )

        # In production, send to proper audit log (e.g., Azure Log Analytics)
        self._audit_log.append(entry)

        if not success:
            logger.warning(
                f"Access denied: {user.user_id} attempted {action.value} on {resource.value}"
            )
        else:
            logger.debug(
                f"Access granted: {user.user_id} performed {action.value} on {resource.value}"
            )

    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        resource: Optional[Resource] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get audit log entries"""
        entries = self._audit_log

        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        if resource:
            entries = [e for e in entries if e.resource == resource.value]

        return entries[-limit:]


# Global RBAC service instance
_rbac_service: Optional[RBACService] = None


def get_rbac_service() -> RBACService:
    """Get or create the RBAC service"""
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService()
    return _rbac_service


def require_permission(resource: Resource, action: Action):
    """
    Dependency to require specific permission.

    Usage:
        @router.post("/agents")
        async def create_agent(
            user: SecurityContext = Depends(require_permission(Resource.AGENTS, Action.CREATE))
        ):
            return {"created": True}
    """

    async def permission_checker(
        user: SecurityContext = Depends(get_current_user),
    ) -> SecurityContext:
        rbac = get_rbac_service()
        rbac.check_permission(user, resource, action)
        return user

    return permission_checker


def check_tenant_access(user: SecurityContext, resource_tenant_id: str) -> bool:
    """
    Check if user can access resources from a specific tenant.

    Enforces tenant isolation unless user is admin.
    """
    # Admins can access any tenant
    if Role.ADMIN in user.roles:
        return True

    # Users can only access their own tenant
    return user.tenant_id == resource_tenant_id


def require_tenant_access(tenant_id_param: str = "tenant_id"):
    """
    Dependency to require tenant access.

    Ensures user can only access resources in their own tenant.
    """

    async def tenant_checker(
        user: SecurityContext = Depends(get_current_user),
        tenant_id: str = None,  # Will be overridden by path parameter
    ) -> SecurityContext:
        if tenant_id and not check_tenant_access(user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this tenant is not permitted",
            )
        return user

    return tenant_checker


# Convenience dependencies for common permissions
require_agent_read = require_permission(Resource.AGENTS, Action.READ)
require_agent_execute = require_permission(Resource.AGENTS, Action.EXECUTE)
require_chat_create = require_permission(Resource.CHAT, Action.CREATE)
require_chat_read = require_permission(Resource.CHAT, Action.READ)
require_memory_read = require_permission(Resource.MEMORY, Action.READ)
require_memory_write = require_permission(Resource.MEMORY, Action.CREATE)
require_memory_delete = require_permission(Resource.MEMORY, Action.DELETE)
require_workflow_read = require_permission(Resource.WORKFLOWS, Action.READ)
require_workflow_execute = require_permission(Resource.WORKFLOWS, Action.EXECUTE)
require_admin = require_permission(Resource.SETTINGS, Action.ADMIN)
