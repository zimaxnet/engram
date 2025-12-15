"""
Engram Workflows Module

Temporal workflow definitions for durable agent execution.
Implements the "Spine" of the Brain + Spine architecture.

Workflows:
- AgentWorkflow: Single turn agent execution
- ConversationWorkflow: Multi-turn long-running conversation
- ApprovalWorkflow: Human-in-the-loop approval

Activities:
- initialize_context_activity: Create enterprise context
- enrich_memory_activity: Load relevant memory
- agent_reasoning_activity: Run LangGraph agent
- persist_memory_activity: Save to memory
- execute_tool_activity: Run agent tools
- validate_response_activity: Validate output
- send_notification_activity: Send notifications
"""

from .activities import (
    MemoryEnrichInput,
    MemoryEnrichOutput,
    MemoryPersistInput,
    MemoryPersistOutput,
    ReasoningInput,
    ReasoningOutput,
    ToolExecutionInput,
    ToolExecutionOutput,
    agent_reasoning_activity,
    enrich_memory_activity,
    execute_tool_activity,
    initialize_context_activity,
    persist_memory_activity,
    send_notification_activity,
    validate_response_activity,
)
from .agent_workflow import (
    AgentWorkflow,
    AgentWorkflowInput,
    AgentWorkflowOutput,
    ApprovalSignal,
    ApprovalWorkflow,
    ConversationTurn,
    ConversationWorkflow,
    UserInputSignal,
)


def _client_module():
    # Lazy import to keep workflow sandbox validation small
    from . import client

    return client


def get_temporal_client(*args, **kwargs):
    return _client_module().get_temporal_client(*args, **kwargs)


def execute_agent_turn(*args, **kwargs):
    return _client_module().execute_agent_turn(*args, **kwargs)


def start_conversation(*args, **kwargs):
    return _client_module().start_conversation(*args, **kwargs)


def send_conversation_message(*args, **kwargs):
    return _client_module().send_conversation_message(*args, **kwargs)


def switch_conversation_agent(*args, **kwargs):
    return _client_module().switch_conversation_agent(*args, **kwargs)


def end_conversation(*args, **kwargs):
    return _client_module().end_conversation(*args, **kwargs)


def get_conversation_history(*args, **kwargs):
    return _client_module().get_conversation_history(*args, **kwargs)


def request_approval(*args, **kwargs):
    return _client_module().request_approval(*args, **kwargs)


def send_approval_decision(*args, **kwargs):
    return _client_module().send_approval_decision(*args, **kwargs)


def get_workflow_status(*args, **kwargs):
    return _client_module().get_workflow_status(*args, **kwargs)

__all__ = [
    # Workflows
    "AgentWorkflow",
    "AgentWorkflowInput",
    "AgentWorkflowOutput",
    "ConversationWorkflow",
    "ConversationTurn",
    "ApprovalWorkflow",
    "ApprovalSignal",
    "UserInputSignal",
    # Activities
    "initialize_context_activity",
    "enrich_memory_activity",
    "agent_reasoning_activity",
    "persist_memory_activity",
    "execute_tool_activity",
    "validate_response_activity",
    "send_notification_activity",
    # Activity I/O types
    "ReasoningInput",
    "ReasoningOutput",
    "MemoryEnrichInput",
    "MemoryEnrichOutput",
    "MemoryPersistInput",
    "MemoryPersistOutput",
    "ToolExecutionInput",
    "ToolExecutionOutput",
    # Client functions
    "get_temporal_client",
    "execute_agent_turn",
    "start_conversation",
    "send_conversation_message",
    "switch_conversation_agent",
    "end_conversation",
    "get_conversation_history",
    "request_approval",
    "send_approval_decision",
    "get_workflow_status",
]
