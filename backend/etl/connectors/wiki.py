import logging
import httpx
from urllib.parse import urlparse
from fastapi import BackgroundTasks

from backend.etl.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)

class WikiConnector:
    """
    Connector for ingesting Wiki pages (Confluence, standard Web Wikis).
    Fetches HTML content and ingests via IngestionService.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def ingest_url(self, url: str, user_id: str, background_tasks: BackgroundTasks) -> dict:
        """
        Fetch a URL and ingest it as a document.
        """
        logger.info(f"WikiConnector: Fetching {url}")
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "").split(";")[0] or "text/html"
            content = response.content
            
            # Extract basic filename from URL
            parsed = urlparse(url)
            filename = parsed.path.split("/")[-1]
            if not filename:
                filename = parsed.netloc.replace(".", "_")
            if "." not in filename:
                filename += ".html"
                
            # Ingest as a document (HTML bytes)
            # We treat HTML as a "document" so Unstructured can partition it intelligently
            result = await ingestion_service.ingest_document(
                content=content,
                filename=filename,
                content_type=content_type,
                user_id=user_id,
                background_tasks=background_tasks
            )
            
            # Enrich with source URL
            # Note: We can't easy update metadata inside ingest_document cleanly without changing its signature 
            # or passing a metadata dict.
            # Ideally IngestionService.ingest_document should accept metadata.
            # For MVP, the 'source' metadata will be overridden by 'document_upload' inside index_chunks_tri.
            # We should probably pass the URL in the filename or handle it better later.
            # But for MVP, capturing the content is key.
            
            logger.info(f"WikiConnector: Successfully ingested {url} as {result.document_id}")
            return result.dict()
            
        except Exception as e:
            logger.error(f"WikiConnector: Failed to ingest {url}: {e}")
            raise

    async def close(self):
        await self.client.aclose()

# Singleton
wiki_connector = WikiConnector()
