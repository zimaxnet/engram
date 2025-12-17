"""
BAU (Business As Usual) endpoints

Provides API for:
- Listing available BAU workflow templates
- Listing recent ingested artifacts
- Starting BAU workflows
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext
from backend.bau.bau_service import (
    bau_service,
    BauFlow,
    BauArtifact,
    StartBauFlowRequest,
    StartBauFlowResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/flows", response_model=List[BauFlow])
async def list_bau_flows(user: SecurityContext = Depends(get_current_user)):
    """
    List available BAU workflow templates.

    These are predefined workflows for common enterprise tasks.
    """
    return bau_service.list_flows()


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
        return await bau_service.list_artifacts(user.user_id, limit, offset)
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
    initial_message = request.initial_message if request else None
    
    try:
        return await bau_service.start_flow(
            flow_id=flow_id, 
            user_id=user.user_id, 
            tenant_id=user.tenant_id, 
            initial_message=initial_message
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start BAU flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start BAU flow: {str(e)}")

