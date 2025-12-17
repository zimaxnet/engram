import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Dict

from pydantic import BaseModel
from fastapi import BackgroundTasks

from backend.etl.processor import processor
from backend.memory.client import memory_client

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

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
    tags: List[str] = []

class ConnectorCreate(BaseModel):
    name: str
    kind: str
    scope: Optional[str] = None
    tags: List[str] = []
    roles: List[str] = []

class ConnectorListResponse(BaseModel):
    sources: List[Connector]

class QueueItem(BaseModel):
    id: str
    name: str
    summary: str
    status: str
    eta_label: str
    # Internal fields not always in API response but useful for state
    created_at: Optional[str] = None
    duration_seconds: float = 90
    doc_count: int = 12
    source_id: Optional[str] = None

class QueueListResponse(BaseModel):
    items: List[QueueItem]

# -----------------------------------------------------------------------------
# Service
# -----------------------------------------------------------------------------

class IngestionService:
    def __init__(self):
        # Adjust path: backend/etl/ingestion_service.py -> parents[1] = backend
        self.state_path = Path(__file__).resolve().parents[1] / "data" / "etl_state.json"
        
    def _default_state(self) -> Dict[str, Any]:
        return {"sources": {}, "queue": []}

    def _load_state(self) -> Dict[str, Any]:
        try:
            if self.state_path.exists():
                with self.state_path.open("r", encoding="utf-8") as fp:
                    return json.load(fp)
        except Exception:
            logger.exception("Failed to load ETL state; falling back to defaults")
        
        default_state = self._default_state()
        self._persist_state(default_state)
        return default_state

    def _persist_state(self, state: Dict[str, Any]) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            with self.state_path.open("w", encoding="utf-8") as fp:
                json.dump(state, fp, indent=2)
        except Exception:
            logger.exception("Failed to persist ETL state")

    def _refresh_queue_progress(self, state: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        sources = state.get("sources", {})
        queue = state.get("queue", [])
        refreshed_queue: List[Dict[str, Any]] = []

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

    def _get_state_with_refresh(self) -> Dict[str, Any]:
        state = self._load_state()
        state = self._refresh_queue_progress(state)
        self._persist_state(state)
        return state

    # Public Methods

    def list_sources(self) -> List[Connector]:
        state = self._get_state_with_refresh()
        sources = state.get("sources", {})
        return [Connector(**value) for value in sources.values()]

    def list_queue(self) -> List[QueueItem]:
        state = self._get_state_with_refresh()
        queue = state.get("queue", [])
        return [QueueItem(**item) for item in queue]

    def create_source(self, payload: ConnectorCreate) -> Connector:
        state = self._load_state()
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
        self._persist_state(state)
        return connector

    def get_source(self, source_id: str) -> Optional[Connector]:
        state = self._get_state_with_refresh()
        connector_data = state.get("sources", {}).get(source_id)
        if not connector_data:
            return None
        return Connector(**connector_data)

    async def ingest_document(self, content: bytes, filename: str, content_type: str, user_id: str, background_tasks: BackgroundTasks) -> IngestResponse:
        logger.info(f"Processing document: {filename}")
        chunks = processor.process_file(content, filename, content_type)

        if not chunks:
            # We raise error here or return failure?
            # To avoid dependency on HTTPException, we can return None or raise standard generic exception
            # But the caller (Validation Service or Agent) needs to handle it.
            # Let's raise ValueError
            raise ValueError("No text content extracted from fule")

        # Background Task Function
        async def index_chunks(chunks_to_index: list, uid: str, fname: str):
            count = 0
            for chunk in chunks_to_index:
                try:
                    chunk_metadata = dict(chunk.get("metadata") or {})
                    etl_source = chunk_metadata.pop("source", None)
                    etl_filename = chunk_metadata.pop("filename", None)

                    await memory_client.add_fact(
                        user_id=uid,
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

        background_tasks.add_task(index_chunks, chunks, user_id, filename)

        return IngestResponse(
            success=True,
            filename=filename,
            chunks_processed=len(chunks),
            message=f"Document accepted. Processing {len(chunks)} chunks in background.",
        )

# Singleton
ingestion_service = IngestionService()
