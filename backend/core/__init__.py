"""
Engram Core Module

Contains foundational components:
- context: 4-Layer Enterprise Context Schema
- config: Configuration management with Key Vault support
"""

from .config import Settings, get_settings
from .context import (
    EnterpriseContext,
    EpisodicState,
    Entity,
    GraphNode,
    MessageRole,
    OperationalState,
    PlanStep,
    PlanStepStatus,
    Role,
    SecurityContext,
    SemanticKnowledge,
    ToolState,
    Turn,
    create_context_from_token,
)

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Context
    "EnterpriseContext",
    "SecurityContext",
    "EpisodicState",
    "SemanticKnowledge",
    "OperationalState",
    "Role",
    "MessageRole",
    "Turn",
    "Entity",
    "GraphNode",
    "PlanStep",
    "PlanStepStatus",
    "ToolState",
    "create_context_from_token",
]
