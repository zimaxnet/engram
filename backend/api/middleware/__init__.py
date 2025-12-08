"""
Engram API Middleware

Provides:
- Authentication via Microsoft Entra ID
- Role-Based Access Control (RBAC)
- Request logging
- Telemetry
"""

from .auth import (
    EntraIDAuth,
    TokenPayload,
    get_auth,
    get_current_user,
    get_optional_user,
    require_roles,
    require_scopes,
    RBACMiddleware,
)

from .rbac import (
    Action,
    Resource,
    RBACService,
    PermissionDenied,
    AuditLogEntry,
    get_rbac_service,
    require_permission,
    check_tenant_access,
    require_tenant_access,
    require_agent_read,
    require_agent_execute,
    require_chat_create,
    require_chat_read,
    require_memory_read,
    require_memory_write,
    require_memory_delete,
    require_workflow_read,
    require_workflow_execute,
    require_admin,
)

from .logging import RequestLoggingMiddleware

__all__ = [
    # Auth
    "EntraIDAuth",
    "TokenPayload",
    "get_auth",
    "get_current_user",
    "get_optional_user",
    "require_roles",
    "require_scopes",
    "RBACMiddleware",
    # RBAC
    "Action",
    "Resource",
    "RBACService",
    "PermissionDenied",
    "AuditLogEntry",
    "get_rbac_service",
    "require_permission",
    "check_tenant_access",
    "require_tenant_access",
    "require_agent_read",
    "require_agent_execute",
    "require_chat_create",
    "require_chat_read",
    "require_memory_read",
    "require_memory_write",
    "require_memory_delete",
    "require_workflow_read",
    "require_workflow_execute",
    "require_admin",
    # Logging
    "RequestLoggingMiddleware",
]
