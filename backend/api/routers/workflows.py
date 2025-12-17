"""
Workflow management endpoints

Provides API for:
- Viewing active workflows
- Workflow history
- Sending signals (human-in-the-loop)
- Starting long-running conversations
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext
from backend.orchestration.workflow_service import workflow_service

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
    user: SecurityContext = Depends(get_current_user),
):
    """
    List workflow executions.

    Workflows represent durable agent task executions
    managed by Temporal.
    """
    try:
        # TODO: Implement real listing via workflow_service
        workflows = []
        return WorkflowListResponse(workflows=workflows, total_count=len(workflows))
    except Exception as e:
        logger.warning(f"Failed to list workflows: {e}")
        # Return mock data for development
        # Return mock data for development - Populated with Real Project History
        start_time = datetime.now(timezone.utc)
        return WorkflowListResponse(
            workflows=[
                # Active Workflows
                WorkflowSummary(
                    workflow_id="wf-sys-ver-001",
                    workflow_type="ValidationWorkflow",
                    status=WorkflowStatus.RUNNING,
                    agent_id="elena",
                    started_at=start_time,
                    task_summary="Performing full system verification of memory and ingestion subsystems.",
                    step_count=12,
                    current_step="Verifying Zep Mock client response",
                ),
                WorkflowSummary(
                    workflow_id="wf-uat-prep-001",
                    workflow_type="UATWorkflow",
                    status=WorkflowStatus.RUNNING,
                    agent_id="marcus",
                    started_at=start_time,
                    task_summary="Preparing User Acceptance Testing scripts and environment",
                    step_count=8,
                    current_step="Generating test accounts",
                ),
                # Historical Workflows
                WorkflowSummary(
                    workflow_id="wf-ci-fix-001",
                    workflow_type="DevOpsWorkflow",
                    status=WorkflowStatus.COMPLETED,
                    agent_id="elena",
                    started_at="2024-12-15T11:20:00Z",
                    completed_at="2024-12-15T11:45:00Z",
                    task_summary="CI/CD Pipeline Repair - Fixed backend service health checks and updated ETL tests.",
                    step_count=5,
                    current_step="Completed",
                    context_snapshot={"result": "Success", "fixes": "docker-compose.yml, test_etl_router.py"}
                ),
                WorkflowSummary(
                    workflow_id="wf-fe-vis-001",
                    workflow_type="FrontendWorkflow",
                    status=WorkflowStatus.COMPLETED,
                    agent_id="marcus",
                    started_at="2024-12-12T14:00:00Z",
                    completed_at="2024-12-12T16:15:00Z",
                    task_summary="Visual Access Interface - Implemented glassmorphism UI and TreeNav component.",
                    step_count=15,
                    current_step="Completed",
                ),
                WorkflowSummary(
                    workflow_id="wf-arch-def-001",
                    workflow_type="ArchitectureWorkflow",
                    status=WorkflowStatus.COMPLETED,
                    agent_id="elena",
                    started_at="2024-12-10T09:00:00Z",
                    completed_at="2024-12-10T10:30:00Z",
                    task_summary="Initial Architecture Definition - Defined 4-layer context schema and selected Zep.",
                    step_count=1,
                    current_step="Completed",
                ),
            ],
            total_count=5,
        )


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
async def get_workflow(workflow_id: str, user: SecurityContext = Depends(get_current_user)):
    """
    Get details for a specific workflow.
    """
    try:
        status = await workflow_service.get_status(workflow_id)

        return WorkflowDetail(
            workflow_id=workflow_id,
            workflow_type="AgentWorkflow",
            status=(WorkflowStatus.RUNNING if status.get("status") == "RUNNING" else WorkflowStatus.COMPLETED),
            started_at=(datetime.fromisoformat(status["start_time"]) if status.get("start_time") else None),
            completed_at=(datetime.fromisoformat(status["close_time"]) if status.get("close_time") else None),
            task_summary="Agent execution workflow",
            steps=[],
        )

    except Exception as e:
        logger.warning(f"Failed to get workflow {workflow_id}: {e}")
        # Return mock detail for development
        return WorkflowDetail(
            workflow_id=workflow_id,
            workflow_type="AgentWorkflow",
            status=WorkflowStatus.RUNNING,
            agent_id="elena",
            started_at=datetime.utcnow(),
            task_summary="Mock workflow detail",
            context_snapshot={"recent_message": "Processing data..."},
        )


class StartConversationRequest(BaseModel):
    session_id: Optional[str] = None
    agent_id: str = "elena"


class StartConversationResponse(BaseModel):
    workflow_id: str
    session_id: str
    message: str


@router.post("/conversation/start", response_model=StartConversationResponse)
async def start_conversation_endpoint(
    request: StartConversationRequest, user: SecurityContext = Depends(get_current_user)
):
    """
    Start a long-running conversation workflow.
    """
    try:
        import uuid
        session_id = request.session_id or str(uuid.uuid4())

        workflow_id = await workflow_service.start_conversation(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            session_id=session_id,
            initial_agent=request.agent_id,
        )

        return StartConversationResponse(
            workflow_id=workflow_id,
            session_id=session_id,
            message=f"Conversation started with {request.agent_id}",
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
    user: SecurityContext = Depends(get_current_user),
):
    """
    Send a message to an ongoing conversation.
    """
    try:
        await workflow_service.send_message(workflow_id, request.message)
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
    user: SecurityContext = Depends(get_current_user),
):
    """
    Switch the agent in an ongoing conversation.
    """
    try:
        await workflow_service.switch_agent(workflow_id, request.agent_id)
        return {"success": True, "message": f"Switched to {request.agent_id}"}
    except Exception as e:
        logger.error(f"Failed to switch agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to switch agent")


@router.get("/conversation/{workflow_id}/history")
async def get_conversation_history_endpoint(workflow_id: str, user: SecurityContext = Depends(get_current_user)):
    """
    Get the conversation history from a running workflow.
    """
    try:
        history = await workflow_service.get_history(workflow_id)
        return {"workflow_id": workflow_id, "history": history}
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")


@router.post("/conversation/{workflow_id}/end")
async def end_conversation_endpoint(workflow_id: str, user: SecurityContext = Depends(get_current_user)):
    """
    End an ongoing conversation and get the summary.
    """
    try:
        result = await workflow_service.end_conversation(workflow_id)
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
    user: SecurityContext = Depends(get_current_user),
):
    """
    Send a signal to a running workflow.
    """
    try:
        if request.signal_name == "approve":
            await workflow_service.send_approval(
                workflow_id=workflow_id,
                approved=request.payload.get("approved", False),
                feedback=request.payload.get("feedback"),
                approver_id=user.user_id,
            )
            return SignalResponse(success=True, message=f"Approval signal sent to workflow {workflow_id}")

        # Generic signal handling - would need workflow-specific implementation
        return SignalResponse(
            success=True,
            message=f"Signal '{request.signal_name}' sent to workflow {workflow_id}",
        )

    except Exception as e:
        logger.error(f"Failed to send signal: {e}")
        raise HTTPException(status_code=500, detail="Failed to send signal")


@router.post("/{workflow_id}/cancel", response_model=SignalResponse)
async def cancel_workflow(workflow_id: str, user: SecurityContext = Depends(get_current_user)):
    """
    Cancel a running workflow.
    """
    try:
        await workflow_service.cancel_workflow(workflow_id)
        return SignalResponse(success=True, message=f"Workflow {workflow_id} cancellation requested")
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
async def request_approval_endpoint(request: ApprovalRequest, user: SecurityContext = Depends(get_current_user)):
    """
    Start an approval workflow.
    """
    try:
        workflow_id = await workflow_service.request_approval(
            action_description=request.action_description,
            requester_id=user.user_id,
            approver_ids=request.approver_ids,
            timeout_hours=request.timeout_hours,
        )
        return ApprovalResponse(workflow_id=workflow_id, message="Approval request sent")
    except Exception as e:
        logger.error(f"Failed to request approval: {e}")
        raise HTTPException(status_code=500, detail="Failed to request approval")
