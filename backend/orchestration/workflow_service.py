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
        List workflows from Temporal.
        
        Args:
            status: Filter by status (running, completed, etc.)
            limit: Pagination limit
            offset: Pagination offset
        
        Returns:
            List of workflow summaries including story workflows.
        """
        try:
            from temporalio.client import WorkflowExecutionStatus
            from datetime import datetime, timezone
            
            client = await get_temporal_client()
            workflows = []
            
            # Map status filter to Temporal status
            temporal_status = None
            if status == "running":
                temporal_status = WorkflowExecutionStatus.RUNNING
            elif status == "completed":
                temporal_status = WorkflowExecutionStatus.COMPLETED
            elif status == "failed":
                temporal_status = WorkflowExecutionStatus.FAILED
            elif status == "waiting":
                # Waiting workflows are typically running but paused
                temporal_status = WorkflowExecutionStatus.RUNNING
            
            # List workflows using Temporal visibility API
            # Note: This requires proper Temporal setup with visibility store
            try:
                # Try to list workflows - this may fail if visibility is not configured
                async for workflow in client.list_workflows(
                    query=f"ExecutionStatus = '{temporal_status.name if temporal_status else 'RUNNING'}'" if temporal_status else None
                ):
                    if len(workflows) >= limit + offset:
                        break
                    
                    try:
                        # Get workflow description
                        handle = client.get_workflow_handle(workflow.id)
                        description = await handle.describe()
                        
                        # Determine workflow type from ID
                        workflow_type = "AgentWorkflow"
                        agent_id = None
                        task_summary = "Agent execution workflow"
                        
                        if workflow.id.startswith("story-"):
                            workflow_type = "StoryWorkflow"
                            agent_id = "sage"  # Story workflows are executed by Sage
                            task_summary = "Story and visual creation"
                            
                            # Try to get story workflow progress
                            try:
                                from backend.workflows.client import get_story_progress
                                progress = await get_story_progress(workflow.id)
                                task_summary = f"Creating story: {progress.get('status', 'in_progress')}"
                            except:
                                pass
                        elif workflow.id.startswith("agent-"):
                            # Extract agent from workflow ID or query
                            agent_id = "elena"  # Default
                            task_summary = "Agent conversation turn"
                        elif workflow.id.startswith("approval-"):
                            workflow_type = "ApprovalWorkflow"
                            task_summary = "Waiting for approval"
                        
                        # Determine status
                        if description.status == WorkflowExecutionStatus.RUNNING:
                            workflow_status = "running"
                        elif description.status == WorkflowExecutionStatus.COMPLETED:
                            workflow_status = "completed"
                        elif description.status == WorkflowExecutionStatus.FAILED:
                            workflow_status = "failed"
                        elif description.status == WorkflowExecutionStatus.CANCELED:
                            workflow_status = "cancelled"
                        else:
                            workflow_status = "unknown"
                        
                        workflows.append({
                            "workflow_id": workflow.id,
                            "workflow_type": workflow_type,
                            "status": workflow_status,
                            "agent_id": agent_id,
                            "started_at": description.start_time.isoformat() if description.start_time else datetime.now(timezone.utc).isoformat(),
                            "completed_at": description.close_time.isoformat() if description.close_time else None,
                            "task_summary": task_summary,
                            "step_count": None,
                            "current_step": None,
                        })
                    except Exception as e:
                        logger.warning(f"Failed to describe workflow {workflow.id}: {e}")
                        continue
                
                # Apply offset and limit
                return workflows[offset:offset + limit]
                
            except Exception as e:
                logger.warning(f"Failed to list workflows from Temporal visibility: {e}")
                # Fallback: return empty list or try alternative method
                return []
                
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
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
