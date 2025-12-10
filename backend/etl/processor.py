"""
Document Processor using Unstructured.io

Handles ingestion of documents (PDF, DOCX, TXT) using the Unstructured library.
Provides partitioning and chunking strategies suitable for RAG.
"""

import logging
from typing import List, Optional
import io

# We import these inside functions to avoid hard hard dependency failures if missing
# but for this file we expect unstructured to be installed.
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.chunking.title import chunk_by_title

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Process documents into chunks for ingestion into Zep memory.
    """

    def __init__(self):
        pass

    def process_file(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: Optional[str] = None,
        strategy: str = "fast"
    ) -> List[dict]:
        """
        Process a file buffer and return a list of text chunks with metadata.
        
        Args:
            file_content: Raw bytes of the file
            filename: Name of the file (for detection)
            content_type: Mime type (optional hint)
            strategy: 'fast' or 'hi_res' (ocr)
        
        Returns:
            List of dicts with 'text' and 'metadata'.
        """
        try:
            # Create a file-like object
            file_obj = io.BytesIO(file_content)
            
            # Partition the document
            logger.info(f"Partitioning file: {filename} using strategy: {strategy}")
            elements = partition(
                file=file_obj,
                file_filename=filename,
                content_type=content_type,
                strategy=strategy,
            )
            
            # Chunk the elements
            # chunk_by_title is a good default for semantic chunking
            logger.info(f"Chunking {len(elements)} elements")
            chunks = chunk_by_title(
                elements,
                max_characters=1000,
                new_after_n_chars=1500,
                combine_text_under_n_chars=500
            )
            
            # Convert to dict format for Zep/API
            processed_chunks = []
            for chunk in chunks:
                processed_chunks.append({
                    "text": str(chunk),
                    "metadata": {
                        "filename": filename,
                        "page_number": chunk.metadata.page_number if hasattr(chunk.metadata, "page_number") else None,
                        "filetype": chunk.metadata.filetype if hasattr(chunk.metadata, "filetype") else None,
                        "source": "unstructured_etl"
                    }
                })
                
            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise

# Singleton
processor = DocumentProcessor()
