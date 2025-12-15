"""
ETL API Endpoints

Provides endpoints for document ingestion and processing.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from pydantic import BaseModel

from backend.core import SecurityContext
from backend.api.middleware.auth import get_current_user
from backend.etl.processor import processor
from backend.memory.client import memory_client

logger = logging.getLogger(__name__)

router = APIRouter()


STATE_PATH = Path(__file__).resolve().parents[2] / "data" / "etl_state.json"


def _default_state() -> dict[str, Any]:
    return {"sources": {}, "queue": []}


def _load_state() -> dict[str, Any]:
    try:
        if STATE_PATH.exists():
            with STATE_PATH.open("r", encoding="utf-8") as fp:
                return json.load(fp)
    except Exception:
        logger.exception("Failed to load ETL state; falling back to defaults")
    default_state = _default_state()
    _persist_state(default_state)
    return default_state


def _persist_state(state: dict[str, Any]) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with STATE_PATH.open("w", encoding="utf-8") as fp:
            json.dump(state, fp, indent=2)
    except Exception:
        logger.exception("Failed to persist ETL state")


def _refresh_queue_progress(state: dict[str, Any]) -> dict[str, Any]:
    now = datetime.utcnow()
    sources = state.get("sources", {})
    queue = state.get("queue", [])
    refreshed_queue: list[dict[str, Any]] = []

    for item in queue:
        created_raw = item.get("created_at")
        duration = float(item.get("duration_seconds", 90))
        try:
            created_at = datetime.fromisoformat(created_raw) if isinstance(created_raw, str) else now
        except Exception:
            created_at = now

        elapsed = (now - created_at).total_seconds()
        status = item.get("status", "running")

        if status != "completed":
            if elapsed >= duration:
                status = "completed"
                item["summary"] = "Completed ingest"
                item["eta_label"] = "done"
                item["status"] = status

                source_id = item.get("source_id")
                source = sources.get(source_id)
                if source:
                    source["status"] = "healthy"
                    source["last_run"] = now.isoformat()
                    source["docs"] = int(source.get("docs", 0)) + int(item.get("doc_count", 12))
                    sources[source_id] = source
            elif elapsed >= duration * 0.5:
                item["status"] = "running"
                item["summary"] = "Parsing and chunking"
                remaining = int(max(duration - elapsed, 1))
                item["eta_label"] = f"{remaining}s"

        refreshed_queue.append(item)

    state["sources"] = sources
    state["queue"] = refreshed_queue
    return state


def _get_state_with_refresh() -> dict[str, Any]:
    state = _load_state()
    state = _refresh_queue_progress(state)
    _persist_state(state)
    return state


class IngestResponse(BaseModel):
    success: bool
    filename: str
    chunks_processed: int
    message: str


class Connector(BaseModel):
    id: str
    name: str
    kind: str
    status: str = "healthy"
    last_run: str = "never"
    docs: int = 0
    tags: list[str] = []


class ConnectorCreate(BaseModel):
    name: str
    kind: str
    scope: str | None = None
    tags: list[str] = []
    roles: list[str] = []


class ConnectorListResponse(BaseModel):
    sources: list[Connector]


class QueueItem(BaseModel):
    id: str
    name: str
    summary: str
    status: str
    eta_label: str


class QueueListResponse(BaseModel):
    items: list[QueueItem]


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

        # Process synchronous for now (simplifies feedback),
        # but in prod this should be a background task or Temporal workflow
        logger.info(f"Processing document: {filename}")
        chunks = processor.process_file(content, filename, content_type)

        if not chunks:
            raise HTTPException(status_code=400, detail="No text content extracted from file")

        # Save to Memory (Zep)
        # We add them as "documents" or facts.
        # ideally Zep has a document collection, but for now we iterate and add facts/nodes.

        async def index_chunks(chunks_to_index, user_id, fname):
            count = 0
            for chunk in chunks_to_index:
                try:
                    chunk_metadata = dict(chunk.get("metadata") or {})
                    # Preserve ingestion provenance while keeping ETL metadata.
                    # Prevent key collisions (e.g. chunk metadata overwriting source/filename).
                    etl_source = chunk_metadata.pop("source", None)
                    etl_filename = chunk_metadata.pop("filename", None)

                    await memory_client.add_fact(
                        user_id=user_id,
                        fact=chunk["text"],
                        metadata={
                            "source": "document_upload",
                            "filename": fname,
                            "etl_source": etl_source,
                            "etl_filename": etl_filename,
                            **chunk_metadata,
                        },
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to index chunk: {e}")
            logger.info(f"Indexed {count} chunks for {fname}")

        # Run indexing in background to return response quickly
        background_tasks.add_task(index_chunks, chunks, user.user_id, filename)

        return IngestResponse(
            success=True,
            filename=filename,
            chunks_processed=len(chunks),
            message=f"Document accepted. Processing {len(chunks)} chunks in background.",
        )

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=ConnectorListResponse)
async def list_sources(user: SecurityContext = Depends(get_current_user)):
    """List configured ingestion sources (connectors)."""
    try:
        state = _get_state_with_refresh()
        sources = state.get("sources", {})
        return ConnectorListResponse(sources=[Connector(**value) for value in sources.values()])
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sources")


@router.post("/sources", response_model=Connector)
async def create_source(payload: ConnectorCreate, user: SecurityContext = Depends(get_current_user)):
    """Create a new ingestion source. In production, persist to DB/connector service."""
    try:
        state = _load_state()

        source_id = f"src-{uuid.uuid4().hex[:8]}"
        connector = Connector(
            id=source_id,
            name=payload.name,
            kind=payload.kind,
            status="indexing",
            last_run="queued",
            docs=0,
            tags=payload.tags or [],
        )
        state.setdefault("sources", {})[source_id] = connector.model_dump()

        queue_item = {
            "id": f"q-{uuid.uuid4().hex[:6]}",
            "source_id": source_id,
            "name": payload.name,
            "summary": "Queued for ingest",
            "status": "running",
            "eta_label": "90s",
            "created_at": datetime.utcnow().isoformat(),
            "duration_seconds": 90,
            "doc_count": 12,
        }

        state.setdefault("queue", []).insert(0, queue_item)
        _persist_state(state)

        return connector
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
        raise HTTPException(status_code=500, detail="Failed to create source")


@router.get("/sources/{source_id}", response_model=Connector)
async def get_source(source_id: str, user: SecurityContext = Depends(get_current_user)):
    """Get a single source."""
    state = _get_state_with_refresh()
    connector = state.get("sources", {}).get(source_id)
    if not connector:
        raise HTTPException(status_code=404, detail="Source not found")
    return Connector(**connector)


@router.get("/queue", response_model=QueueListResponse)
async def list_queue(user: SecurityContext = Depends(get_current_user)):
    """List ingest queue items."""
    try:
        state = _get_state_with_refresh()
        queue = state.get("queue", [])
        return QueueListResponse(items=[QueueItem(**item) for item in queue])
    except Exception as e:
        logger.error(f"Failed to list queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to list queue")
