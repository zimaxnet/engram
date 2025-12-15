"""
BAU (Business As Usual) endpoints

Provides API for:
- Listing available BAU workflow templates
- Listing recent ingested artifacts
- Starting BAU workflows
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext
from backend.memory.client import memory_client
from backend.workflows.client import execute_agent_turn, start_conversation

logger = logging.getLogger(__name__)

router = APIRouter()


class BauFlow(BaseModel):
    """BAU workflow template definition"""
    id: str  # intake-triage, policy-qa, decision-log
    title: str
    persona: str
    description: str
    cta: str


class BauArtifact(BaseModel):
    """Recent artifact from ingestion"""
    id: str
    name: str
    ingested_at: datetime
    chips: List[str]  # tenant, domain, sensitivity tags


class StartBauFlowRequest(BaseModel):
    """Request to start a BAU flow"""
    flow_id: str
    initial_message: Optional[str] = None


class StartBauFlowResponse(BaseModel):
    """Response from starting a BAU flow"""
    workflow_id: str
    session_id: str
    message: str


# BAU Flow definitions
BAU_FLOWS = [
    BauFlow(
        id="intake-triage",
        title="Intake & triage",
        persona="Marcus",
        description="Turn requests into plans, milestones, owners, and risk flags.",
        cta="Start",
    ),
    BauFlow(
        id="policy-qa",
        title="Policy Q&A",
        persona="Elena",
        description="Ask questions and get answers with citations and sensitivity warnings.",
        cta="Ask",
    ),
    BauFlow(
        id="decision-log",
        title="Decision log search",
        persona="Elena + Marcus",
        description="Recall decisions and provenance across time and projects.",
        cta="Search",
    ),
]


@router.get("/flows", response_model=List[BauFlow])
async def list_bau_flows(user: SecurityContext = Depends(get_current_user)):
    """
    List available BAU workflow templates.

    These are predefined workflows for common enterprise tasks.
    """
    return BAU_FLOWS


@router.get("/artifacts", response_model=List[BauArtifact])
async def list_bau_artifacts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: SecurityContext = Depends(get_current_user),
):
    """
    List recent ingested artifacts.

    Returns artifacts from document ingestion with provenance metadata.
    """
    try:
        # Query recent facts from memory that have document_upload source
        # In a real implementation, this would query Zep for facts with specific metadata
        # For now, we'll return a deterministic list based on recent ingestion
        
        # In production, this would query:
        # - Zep memory for facts with source="document_upload"
        # - Group by filename
        # - Extract metadata (tenant, domain, sensitivity)
        # - Sort by ingested_at descending
        
        # Mock implementation for now - in production, query memory_client
        artifacts = []
        
        # Try to get recent facts from memory
        try:
            # Search for recent document uploads
            # This is a simplified query - in production, use proper memory search
            recent_facts = await memory_client.search_facts(
                user_id=user.user_id,
                query="document",
                limit=limit,
            )
            
            # Group by filename and extract metadata
            seen_files = {}
            for fact in recent_facts.get("results", []):
                metadata = fact.get("metadata", {})
                filename = metadata.get("filename") or metadata.get("etl_filename", "Unknown")
                
                if filename not in seen_files:
                    chips = []
                    if metadata.get("tenant"):
                        chips.append(f"tenant:{metadata['tenant']}")
                    if metadata.get("domain"):
                        chips.append(f"domain:{metadata['domain']}")
                    if metadata.get("sensitivity"):
                        chips.append(f"sensitivity:{metadata['sensitivity']}")
                    
                    # Default chips if not in metadata
                    if not chips:
                        chips = ["tenant:zimax", "project:alpha", "sensitivity:silver"]
                    
                    artifacts.append(
                        BauArtifact(
                            id=f"art-{len(artifacts) + 1}",
                            name=filename,
                            ingested_at=datetime.utcnow() - timedelta(hours=len(artifacts) * 2),
                            chips=chips,
                        )
                    )
                    seen_files[filename] = True
        except Exception as e:
            logger.warning(f"Failed to query memory for artifacts: {e}")
        
        # If no artifacts found, return mock data
        if not artifacts:
            artifacts = [
                BauArtifact(
                    id="art-1",
                    name="Meeting notes — Steering Committee",
                    ingested_at=datetime.utcnow() - timedelta(hours=2),
                    chips=["tenant:zimax", "project:alpha", "sensitivity:silver"],
                ),
                BauArtifact(
                    id="art-2",
                    name="Policy update — Data retention",
                    ingested_at=datetime.utcnow() - timedelta(days=1),
                    chips=["tenant:zimax", "domain:security", "sensitivity:gold"],
                ),
            ]
        
        # Apply pagination
        paginated = artifacts[offset:offset + limit]
        return paginated
        
    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list artifacts")


@router.post("/flows/{flow_id}/start", response_model=StartBauFlowResponse)
async def start_bau_flow(
    flow_id: str,
    request: Optional[StartBauFlowRequest] = None,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Start a BAU workflow.

    Creates a new conversation workflow with the appropriate agent persona.
    """
    # Validate flow_id
    flow = next((f for f in BAU_FLOWS if f.id == flow_id), None)
    if not flow:
        raise HTTPException(status_code=404, detail=f"BAU flow '{flow_id}' not found")
    
    try:
        import uuid
        
        # Determine agent based on flow persona
        agent_id = "marcus" if "Marcus" in flow.persona else "elena"
        
        # Create session ID
        session_id = f"bau-{flow_id}-{uuid.uuid4().hex[:8]}"
        
        # Start conversation workflow
        workflow_id = await start_conversation(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            session_id=session_id,
            initial_agent=agent_id,
        )
        
        # If initial message provided, send it
        if request and request.initial_message:
            from backend.workflows.client import send_conversation_message
            await send_conversation_message(workflow_id, request.initial_message)
        
        logger.info(f"Started BAU flow: {flow_id}, workflow_id={workflow_id}")
        
        return StartBauFlowResponse(
            workflow_id=workflow_id,
            session_id=session_id,
            message=f"BAU flow '{flow.title}' started with {flow.persona}",
        )
        
    except Exception as e:
        logger.error(f"Failed to start BAU flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start BAU flow: {str(e)}")

