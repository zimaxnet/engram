"""
Audit Logging Module

Provides comprehensive audit trail for:
- Security events (login, logout, access denied)
- Agent actions (tool calls, responses)
- Data access (memory queries, document ingestion)
- Administrative actions (config changes, user management)

NIST AI RMF: MANAGE 4.2 (Audit), GOVERN 1.2 (Accountability)
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps

logger = logging.getLogger("audit")


class AuditEventType(str, Enum):
    """Categories of auditable events."""
    # Security events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTH_LOGOUT = "auth.logout"
    ACCESS_DENIED = "auth.access_denied"
    TOKEN_EXPIRED = "auth.token_expired"
    
    # Agent events
    AGENT_INVOKED = "agent.invoked"
    AGENT_RESPONSE = "agent.response"
    AGENT_TOOL_CALL = "agent.tool_call"
    AGENT_ERROR = "agent.error"
    
    # Memory events
    MEMORY_SEARCH = "memory.search"
    MEMORY_ADD = "memory.add"
    MEMORY_UPDATE = "memory.update"
    MEMORY_DELETE = "memory.delete"
    
    # ETL events
    ETL_INGEST_START = "etl.ingest_start"
    ETL_INGEST_COMPLETE = "etl.ingest_complete"
    ETL_INGEST_FAILURE = "etl.ingest_failure"
    ETL_CLASSIFICATION = "etl.classification"
    
    # Admin events
    ADMIN_CONFIG_CHANGE = "admin.config_change"
    ADMIN_USER_CREATE = "admin.user_create"
    ADMIN_USER_UPDATE = "admin.user_update"
    ADMIN_ROLE_CHANGE = "admin.role_change"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    FEATURE_FLAG_CHANGE = "system.feature_flag_change"


@dataclass
class AuditEvent:
    """
    Structured audit event record.
    
    All fields are designed for SIEM integration and compliance reporting.
    """
    event_type: AuditEventType
    timestamp: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    agent_id: Optional[str]
    action: str
    resource: Optional[str]
    resource_type: Optional[str]
    outcome: str  # "success", "failure", "denied"
    details: dict
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string for structured logging."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Audit logging service with multiple output targets.
    
    Outputs:
    - Python logging (structured JSON)
    - Azure Monitor (via OpenTelemetry)
    - File (for local compliance)
    """
    
    def __init__(self, app_name: str = "engram"):
        self.app_name = app_name
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure the audit logger."""
        self._logger = logging.getLogger("audit")
        self._logger.setLevel(logging.INFO)
        
        # Ensure JSON formatting for structured logs
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        
        if not self._logger.handlers:
            self._logger.addHandler(handler)
    
    def log(
        self,
        event_type: AuditEventType,
        action: str,
        outcome: str = "success",
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_type: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Category of event
            action: Specific action taken
            outcome: "success", "failure", or "denied"
            user_id: User performing the action
            tenant_id: Tenant scope
            session_id: Session identifier
            request_id: Request trace ID
            agent_id: AI agent (if applicable)
            resource: Resource being accessed
            resource_type: Type of resource
            details: Additional context
            ip_address: Client IP
            user_agent: Client user agent
        """
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            request_id=request_id,
            agent_id=agent_id,
            action=action,
            resource=resource,
            resource_type=resource_type,
            outcome=outcome,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Log as structured JSON
        log_level = logging.WARNING if outcome == "failure" else logging.INFO
        if outcome == "denied":
            log_level = logging.WARNING
        
        self._logger.log(log_level, event.to_json())
        
        # TODO: Send to Azure Monitor
        # self._send_to_azure_monitor(event)
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        outcome: str,
        details: dict = None,
        ip_address: str = None,
    ):
        """Convenience method for security events."""
        self.log(
            event_type=event_type,
            action=event_type.value.split(".")[-1],
            outcome=outcome,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
        )
    
    def log_agent_action(
        self,
        agent_id: str,
        action: str,
        user_id: str,
        details: dict = None,
        outcome: str = "success",
    ):
        """Convenience method for agent actions."""
        self.log(
            event_type=AuditEventType.AGENT_INVOKED,
            action=action,
            outcome=outcome,
            user_id=user_id,
            agent_id=agent_id,
            details=details,
        )
    
    def log_memory_access(
        self,
        event_type: AuditEventType,
        user_id: str,
        query: str = None,
        result_count: int = 0,
    ):
        """Convenience method for memory operations."""
        self.log(
            event_type=event_type,
            action="search" if "search" in event_type.value else event_type.value.split(".")[-1],
            outcome="success",
            user_id=user_id,
            resource_type="memory",
            details={"query": query, "result_count": result_count},
        )


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions
def audit_log(
    event_type: AuditEventType,
    action: str,
    **kwargs
):
    """Quick audit log function."""
    get_audit_logger().log(event_type, action, **kwargs)


def audit_security(event_type: AuditEventType, user_id: str, outcome: str, **kwargs):
    """Quick security audit log."""
    get_audit_logger().log_security_event(event_type, user_id, outcome, **kwargs)


# Decorator for auditing function calls
def audited(event_type: AuditEventType, action: str = None):
    """
    Decorator to automatically audit function calls.
    
    Usage:
        @audited(AuditEventType.MEMORY_SEARCH, action="semantic_search")
        async def search_memory(query: str, user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to extract user_id from kwargs or first arg
            user_id = kwargs.get("user_id") or (args[0] if args else None)
            
            try:
                result = await func(*args, **kwargs)
                audit_log(
                    event_type,
                    action or func.__name__,
                    user_id=str(user_id) if user_id else None,
                    outcome="success",
                )
                return result
            except Exception as e:
                audit_log(
                    event_type,
                    action or func.__name__,
                    user_id=str(user_id) if user_id else None,
                    outcome="failure",
                    details={"error": str(e)},
                )
                raise
        return wrapper
    return decorator
