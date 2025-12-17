import logging
from typing import Optional, List, Dict, Any

from backend.workflows.client import (
    get_temporal_client,
    execute_agent_turn,
    start_conversation,
    send_conversation_message,
    switch_conversation_agent,
    end_conversation,
    get_conversation_history,
    request_approval,
    send_approval_decision,
    get_workflow_status as client_get_status
)

logger = logging.getLogger(__name__)

class WorkflowService:
    """
    Service layer for orchestration and workflow management.
    Wraps the backend.workflows.client functions.
    """

    async def get_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get flattened status of a workflow."""
        return await client_get_status(workflow_id)

    async def list_workflows(self, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List workflows.
        
        Args:
            status: Filter by status (running, completed, etc.)
            limit: Pagination limit
            offset: Pagination offset
        
        Returns:
            List of workflow summaries.
        """
        # TODO: Implement real listing via Temporal client visibility API
        # For now return empty or mock, similar to router logic
        return []

    async def start_conversation(self, user_id: str, tenant_id: str, session_id: str, initial_agent: str = "elena") -> str:
        return await start_conversation(user_id, tenant_id, session_id, initial_agent)

    async def send_message(self, workflow_id: str, message: str) -> None:
        await send_conversation_message(workflow_id, message)

    async def switch_agent(self, workflow_id: str, agent_id: str) -> None:
        await switch_conversation_agent(workflow_id, agent_id)

    async def end_conversation(self, workflow_id: str) -> Dict[str, Any]:
        return await end_conversation(workflow_id)

    async def get_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        return await get_conversation_history(workflow_id)
    
    async def request_approval(self, action_description: str, requester_id: str, approver_ids: List[str], timeout_hours: int = 24) -> str:
        return await request_approval(action_description, requester_id, approver_ids, timeout_hours)

    async def send_approval(self, workflow_id: str, approved: bool, feedback: Optional[str] = None, approver_id: Optional[str] = None) -> None:
        await send_approval_decision(workflow_id, approved, feedback, approver_id)

    async def cancel_workflow(self, workflow_id: str) -> None:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.cancel()


# Singleton instance
workflow_service = WorkflowService()
