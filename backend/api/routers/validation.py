"""
Validation and Golden Thread endpoints

Provides API for:
- Golden thread dataset management
- Running golden thread validation suites
- Retrieving validation results and evidence bundles
"""

import logging
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext
from backend.validation.validation_service import (
    validation_service,
    GoldenDataset,
    GoldenRun,
    GoldenRunSummary,
    GoldenCheck
)

logger = logging.getLogger(__name__)

router = APIRouter()

class RunGoldenThreadRequest(BaseModel):
    """Request to run golden thread"""
    dataset_id: str
    mode: Literal["deterministic", "acceptance"] = "deterministic"

@router.get("/datasets", response_model=List[GoldenDataset])
async def list_golden_datasets(user: SecurityContext = Depends(get_current_user)):
    """
    List available golden datasets for validation.
    """
    return validation_service.list_datasets()

@router.get("/runs/latest", response_model=Optional[GoldenRun])
async def get_latest_golden_run(user: SecurityContext = Depends(get_current_user)):
    """
    Get the latest golden thread run.
    """
    return validation_service.get_latest_run()

@router.get("/runs/{run_id}", response_model=GoldenRun)
async def get_golden_run(run_id: str, user: SecurityContext = Depends(get_current_user)):
    """
    Get a specific golden thread run by ID.
    """
    run = validation_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Golden run '{run_id}' not found")
    return run

@router.post("/run", response_model=GoldenRun)
async def run_golden_thread(
    request: RunGoldenThreadRequest,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Trigger a golden thread validation run.
    """
    try:
        return await validation_service.run_golden_thread(request.dataset_id, request.mode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run golden thread: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run golden thread: {str(e)}")

@router.get("/runs/{run_id}/evidence")
async def download_evidence_bundle(
    run_id: str,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Download evidence bundle for a golden thread run.
    """
    run = validation_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Golden run '{run_id}' not found")
    
    # Build evidence bundle
    evidence = {
        "run_id": run.summary.run_id,
        "dataset_id": run.summary.dataset_id,
        "status": run.summary.status,
        "checks": [
            {
                "id": check.id,
                "name": check.name,
                "status": check.status,
                "evidence": check.evidence_summary,
            }
            for check in run.checks
        ],
        "traceability": {
            "trace_id": run.summary.trace_id,
            "workflow_id": run.summary.workflow_id,
            "session_id": run.summary.session_id,
        },
        "narrative": run.narrative,
        "timestamp": run.summary.ended_at or run.summary.started_at,
    }
    
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        content=evidence,
        headers={
            "Content-Disposition": f'attachment; filename="golden-thread-{run_id}.json"',
        },
    )

