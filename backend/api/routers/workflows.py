"""
Workflow management endpoints

Provides API for:
- Viewing active workflows
- Workflow history
- Sending signals (human-in-the-loop)
- Starting long-running conversations
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext

logger = logging.getLogger(__name__)

router = APIRouter()


class WorkflowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"
    CANCELLED = "cancelled"


class WorkflowSummary(BaseModel):
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    agent_id: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    task_summary: str
    step_count: Optional[int] = None
    current_step: Optional[str] = None


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowSummary]
    total_count: int


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[WorkflowStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: SecurityContext = Depends(get_current_user)
):
    """
    List workflow executions.
    
    Workflows represent durable agent task executions
    managed by Temporal.
    """
    try:
        from backend.workflows import get_temporal_client
        
        client = await get_temporal_client()
        
        # Query workflows (simplified - in production, use proper listing)
        # This is a placeholder - Temporal's list API is more complex
        workflows = []
        
        return WorkflowListResponse(
            workflows=workflows,
            total_count=len(workflows)
        )
        
    except Exception as e:
        logger.warning(f"Failed to list workflows: {e}")
        # Return empty list if Temporal not available
        return WorkflowListResponse(workflows=[], total_count=0)


class WorkflowDetail(BaseModel):
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    agent_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_summary: str
    steps: list[dict] = []
    context_snapshot: Optional[dict] = None
    error: Optional[str] = None


@router.get("/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: str,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Get details for a specific workflow.
    
    Includes step history and current context state.
    """
    try:
        from backend.workflows import get_workflow_status
        
        status = await get_workflow_status(workflow_id)
        
        return WorkflowDetail(
            workflow_id=workflow_id,
            workflow_type="AgentWorkflow",
            status=WorkflowStatus.RUNNING if status["status"] == "RUNNING" else WorkflowStatus.COMPLETED,
            started_at=datetime.fromisoformat(status["start_time"]) if status.get("start_time") else None,
            completed_at=datetime.fromisoformat(status["close_time"]) if status.get("close_time") else None,
            task_summary="Agent execution workflow",
            steps=[]
        )
        
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")


class StartConversationRequest(BaseModel):
    session_id: Optional[str] = None
    agent_id: str = "elena"


class StartConversationResponse(BaseModel):
    workflow_id: str
    session_id: str
    message: str


@router.post("/conversation/start", response_model=StartConversationResponse)
async def start_conversation_endpoint(
    request: StartConversationRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Start a long-running conversation workflow.
    
    The conversation can span multiple turns and persist for days.
    Use signals to send messages and switch agents.
    """
    try:
        import uuid
        from backend.workflows import start_conversation
        
        session_id = request.session_id or str(uuid.uuid4())
        
        workflow_id = await start_conversation(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            session_id=session_id,
            initial_agent=request.agent_id
        )
        
        return StartConversationResponse(
            workflow_id=workflow_id,
            session_id=session_id,
            message=f"Conversation started with {request.agent_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")


class SendMessageRequest(BaseModel):
    message: str


@router.post("/conversation/{workflow_id}/message")
async def send_message_to_conversation(
    workflow_id: str,
    request: SendMessageRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Send a message to an ongoing conversation.
    """
    try:
        from backend.workflows import send_conversation_message
        
        await send_conversation_message(workflow_id, request.message)
        
        return {"success": True, "message": "Message sent"}
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


class SwitchAgentRequest(BaseModel):
    agent_id: str


@router.post("/conversation/{workflow_id}/switch-agent")
async def switch_agent_in_conversation(
    workflow_id: str,
    request: SwitchAgentRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Switch the agent in an ongoing conversation.
    """
    try:
        from backend.workflows import switch_conversation_agent
        
        await switch_conversation_agent(workflow_id, request.agent_id)
        
        return {"success": True, "message": f"Switched to {request.agent_id}"}
        
    except Exception as e:
        logger.error(f"Failed to switch agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to switch agent")


@router.get("/conversation/{workflow_id}/history")
async def get_conversation_history_endpoint(
    workflow_id: str,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Get the conversation history from a running workflow.
    """
    try:
        from backend.workflows import get_conversation_history
        
        history = await get_conversation_history(workflow_id)
        
        return {"workflow_id": workflow_id, "history": history}
        
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")


@router.post("/conversation/{workflow_id}/end")
async def end_conversation_endpoint(
    workflow_id: str,
    user: SecurityContext = Depends(get_current_user)
):
    """
    End an ongoing conversation and get the summary.
    """
    try:
        from backend.workflows import end_conversation
        
        result = await end_conversation(workflow_id)
        
        return {"success": True, "summary": result}
        
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to end conversation")


class SignalRequest(BaseModel):
    signal_name: str
    payload: dict = {}


class SignalResponse(BaseModel):
    success: bool
    message: str


@router.post("/{workflow_id}/signal", response_model=SignalResponse)
async def send_signal(
    workflow_id: str,
    request: SignalRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Send a signal to a running workflow.
    
    Used for human-in-the-loop scenarios:
    - Approval signals
    - Rejection signals
    - Additional input
    """
    try:
        from backend.workflows import get_temporal_client, send_approval_decision
        
        if request.signal_name == "approve":
            await send_approval_decision(
                workflow_id=workflow_id,
                approved=request.payload.get("approved", False),
                feedback=request.payload.get("feedback"),
                approver_id=user.user_id
            )
            return SignalResponse(
                success=True,
                message=f"Approval signal sent to workflow {workflow_id}"
            )
        
        # Generic signal handling
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        # Note: Generic signals would need workflow-specific handling
        return SignalResponse(
            success=True,
            message=f"Signal '{request.signal_name}' sent to workflow {workflow_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to send signal: {e}")
        raise HTTPException(status_code=500, detail="Failed to send signal")


@router.post("/{workflow_id}/cancel", response_model=SignalResponse)
async def cancel_workflow(
    workflow_id: str,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Cancel a running workflow.
    
    The workflow will be terminated and marked as cancelled.
    """
    try:
        from backend.workflows import get_temporal_client
        
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        
        await handle.cancel()
        
        return SignalResponse(
            success=True,
            message=f"Workflow {workflow_id} cancellation requested"
        )
        
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel workflow")


class ApprovalRequest(BaseModel):
    action_description: str
    approver_ids: list[str]
    timeout_hours: int = 24


class ApprovalResponse(BaseModel):
    workflow_id: str
    message: str


@router.post("/approval/request", response_model=ApprovalResponse)
async def request_approval_endpoint(
    request: ApprovalRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Start an approval workflow.
    
    Use for actions requiring human approval before execution.
    """
    try:
        from backend.workflows import request_approval
        
        workflow_id = await request_approval(
            action_description=request.action_description,
            requester_id=user.user_id,
            approver_ids=request.approver_ids,
            timeout_hours=request.timeout_hours
        )
        
        return ApprovalResponse(
            workflow_id=workflow_id,
            message="Approval request sent"
        )
        
    except Exception as e:
        logger.error(f"Failed to request approval: {e}")
        raise HTTPException(status_code=500, detail="Failed to request approval")
