"""
Temporal Client

Provides convenience functions for starting and interacting with workflows.
Used by the API layer to execute agent workflows.
"""

import logging
import uuid
from datetime import timedelta
from typing import Optional

from temporalio.client import Client

from backend.core import get_settings
from backend.workflows.agent_workflow import (
    AgentWorkflow,
    AgentWorkflowInput,
    AgentWorkflowOutput,
    ApprovalSignal,
    ApprovalWorkflow,
    ConversationWorkflow,
)

logger = logging.getLogger(__name__)

# Global client instance
_client: Optional[Client] = None


async def get_temporal_client() -> Client:
    """Get or create the Temporal client"""
    global _client
    
    if _client is None:
        settings = get_settings()
        host_parts = settings.temporal_host.split(":")
        host = host_parts[0]
        port = int(host_parts[1]) if len(host_parts) > 1 else 7233
        
        _client = await Client.connect(
            f"{host}:{port}",
            namespace=settings.temporal_namespace,
        )
        logger.info(f"Temporal client connected: {settings.temporal_host}")
    
    return _client


async def execute_agent_turn(
    user_id: str,
    tenant_id: str,
    session_id: str,
    agent_id: str,
    user_message: str,
    timeout_seconds: int = 120
) -> AgentWorkflowOutput:
    """
    Execute a single agent turn via Temporal workflow.
    
    This is the main entry point for the API to execute agent requests
    with durable execution guarantees.
    
    Args:
        user_id: User identifier
        tenant_id: Tenant identifier
        session_id: Session identifier
        agent_id: Agent to use (elena/marcus)
        user_message: User's message
        timeout_seconds: Maximum execution time
        
    Returns:
        AgentWorkflowOutput with response and metadata
    """
    settings = get_settings()
    client = await get_temporal_client()
    
    # Generate workflow ID
    workflow_id = f"agent-{session_id}-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Starting agent workflow: {workflow_id}")
    
    # Start workflow
    handle = await client.start_workflow(
        AgentWorkflow.run,
        AgentWorkflowInput(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            agent_id=agent_id,
            user_message=user_message
        ),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
        execution_timeout=timedelta(seconds=timeout_seconds),
    )
    
    # Wait for result
    result = await handle.result()
    
    logger.info(f"Workflow completed: {workflow_id}, success={result.success}")
    
    return result


async def start_conversation(
    user_id: str,
    tenant_id: str,
    session_id: str,
    initial_agent: str = "elena"
) -> str:
    """
    Start a long-running conversation workflow.
    
    Returns the workflow ID for subsequent interactions.
    """
    settings = get_settings()
    client = await get_temporal_client()
    
    workflow_id = f"conversation-{session_id}"
    
    await client.start_workflow(
        ConversationWorkflow.run,
        args=[user_id, tenant_id, session_id, initial_agent],
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    
    logger.info(f"Started conversation workflow: {workflow_id}")
    
    return workflow_id


async def send_conversation_message(
    workflow_id: str,
    message: str
) -> None:
    """
    Send a message to an ongoing conversation.
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    
    await handle.signal(ConversationWorkflow.send_message, message)
    
    logger.info(f"Sent message to conversation: {workflow_id}")


async def switch_conversation_agent(
    workflow_id: str,
    agent_id: str
) -> None:
    """
    Switch the agent in an ongoing conversation.
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    
    await handle.signal(ConversationWorkflow.switch_agent, agent_id)
    
    logger.info(f"Switched agent to {agent_id} in conversation: {workflow_id}")


async def end_conversation(workflow_id: str) -> dict:
    """
    End an ongoing conversation and get the summary.
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    
    await handle.signal(ConversationWorkflow.end_conversation)
    
    # Wait for workflow to complete
    result = await handle.result()
    
    logger.info(f"Conversation ended: {workflow_id}")
    
    return result


async def get_conversation_history(workflow_id: str) -> list[dict]:
    """
    Get the conversation history from a running workflow.
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    
    return await handle.query(ConversationWorkflow.get_history)


async def request_approval(
    action_description: str,
    requester_id: str,
    approver_ids: list[str],
    timeout_hours: int = 24
) -> str:
    """
    Start an approval workflow.
    
    Returns the workflow ID to check status or send approval.
    """
    settings = get_settings()
    client = await get_temporal_client()
    
    workflow_id = f"approval-{uuid.uuid4().hex[:8]}"
    
    await client.start_workflow(
        ApprovalWorkflow.run,
        args=[action_description, requester_id, approver_ids, timeout_hours],
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    
    logger.info(f"Started approval workflow: {workflow_id}")
    
    return workflow_id


async def send_approval_decision(
    workflow_id: str,
    approved: bool,
    feedback: Optional[str] = None,
    approver_id: Optional[str] = None
) -> None:
    """
    Send an approval decision to a pending workflow.
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    
    await handle.signal(
        ApprovalWorkflow.approve,
        ApprovalSignal(
            approved=approved,
            feedback=feedback,
            approver_id=approver_id
        )
    )
    
    logger.info(f"Sent approval decision to: {workflow_id}, approved={approved}")


async def get_workflow_status(workflow_id: str) -> dict:
    """
    Get the status of any workflow.
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    
    description = await handle.describe()
    
    return {
        "workflow_id": workflow_id,
        "status": str(description.status),
        "start_time": description.start_time.isoformat() if description.start_time else None,
        "close_time": description.close_time.isoformat() if description.close_time else None,
    }

