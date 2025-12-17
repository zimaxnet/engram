import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks

from backend.core import SecurityContext
from backend.api.middleware.auth import get_current_user
from backend.etl.ingestion_service import (
    ingestion_service,
    IngestResponse,
    Connector,
    ConnectorCreate,
    ConnectorListResponse,
    QueueListResponse,
    QueueItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: SecurityContext = Depends(get_current_user),
):
    """
    Ingest a document (PDF, TXT, DOCX) into the knowledge graph.

    The document is:
    1. Uploaded
    2. Partitioned and chunked (Unstructured.io)
    3. Indexed into Zep Memory (Vector + Graph)
    """
    try:
        filename = file.filename
        content_type = file.content_type

        # Read file content
        content = await file.read()

        return await ingestion_service.ingest_document(
            content=content,
            filename=filename,
            content_type=content_type,
            user_id=user.user_id,
            background_tasks=background_tasks
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=ConnectorListResponse)
async def list_sources(user: SecurityContext = Depends(get_current_user)):
    """List configured ingestion sources (connectors)."""
    try:
        sources = ingestion_service.list_sources()
        # Wrap list in response model if needed, but ConnectorListResponse expects `sources` list
        return ConnectorListResponse(sources=sources)
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sources")


@router.post("/sources", response_model=Connector)
async def create_source(payload: ConnectorCreate, user: SecurityContext = Depends(get_current_user)):
    """Create a new ingestion source. In production, persist to DB/connector service."""
    try:
        return ingestion_service.create_source(payload)
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
        raise HTTPException(status_code=500, detail="Failed to create source")


@router.get("/sources/{source_id}", response_model=Connector)
async def get_source(source_id: str, user: SecurityContext = Depends(get_current_user)):
    """Get a single source."""
    connector = ingestion_service.get_source(source_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Source not found")
    return connector


@router.get("/queue", response_model=QueueListResponse)
async def list_queue(user: SecurityContext = Depends(get_current_user)):
    """List ingest queue items."""
    try:
        items = ingestion_service.list_queue()
        return QueueListResponse(items=items)
    except Exception as e:
        logger.error(f"Failed to list queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to list queue")
