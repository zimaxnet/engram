"""
ETL API Endpoints

Provides endpoints for document ingestion and processing.
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from pydantic import BaseModel

from backend.core import SecurityContext
from backend.api.middleware.auth import get_current_user
from backend.etl.processor import processor
from backend.memory.client import memory_client

logger = logging.getLogger(__name__)

router = APIRouter()


class IngestResponse(BaseModel):
    success: bool
    filename: str
    chunks_processed: int
    message: str


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
            raise HTTPException(
                status_code=400, detail="No text content extracted from file"
            )

        # Save to Memory (Zep)
        # We add them as "documents" or facts.
        # ideally Zep has a document collection, but for now we iterate and add facts/nodes.

        async def index_chunks(chunks_to_index, user_id, fname):
            count = 0
            for chunk in chunks_to_index:
                try:
                    await memory_client.add_fact(
                        user_id=user_id,
                        fact=chunk["text"],
                        metadata={
                            "source": "document_upload",
                            "filename": fname,
                            **chunk["metadata"],
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
