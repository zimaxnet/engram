"""
Document Processor using Unstructured.io

Handles ingestion of documents (PDF, DOCX, TXT) using the Unstructured library.
Provides partitioning and chunking strategies suitable for RAG.
"""

import logging
from typing import List, Optional
import io

# Unstructured is an optional dependency in some dev/test environments.
# Keep module import safe so tests can monkeypatch these symbols.
try:
    from unstructured.partition.auto import partition  # type: ignore
    from unstructured.chunking.title import chunk_by_title  # type: ignore
except Exception:  # pragma: no cover
    partition = None  # type: ignore
    chunk_by_title = None  # type: ignore

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
        strategy: str = "fast",
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
            if partition is None or chunk_by_title is None:
                raise RuntimeError(
                    "Unstructured is not installed. Install 'unstructured[all-docs]' to enable document ingestion."
                )

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
                combine_text_under_n_chars=500,
            )

            # Convert to dict format for Zep/API
            processed_chunks = []
            for chunk in chunks:
                processed_chunks.append(
                    {
                        "text": str(chunk),
                        "metadata": {
                            "filename": filename,
                            "page_number": (
                                chunk.metadata.page_number if hasattr(chunk.metadata, "page_number") else None
                            ),
                            "filetype": (chunk.metadata.filetype if hasattr(chunk.metadata, "filetype") else None),
                            "source": "unstructured_etl",
                        },
                    }
                )

            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise

    def process_text(
        self,
        text: str,
        filename: str,
        metadata: Optional[dict] = None,
    ) -> List[dict]:
        """
        Process raw text string into chunks.
        Useful for connectors that extract text directly (Wiki, Tickets).
        """
        if chunk_by_title is None:
             raise RuntimeError("Unstructured not installed.")

        try:
            from unstructured.documents.elements import Text
            
            # Create a simple element from the text
            # For complex text with structure, we might want to use partition_text
            # but for now, we'll just treat it as one element and let chunker split it
            # if it's too large.
            # actually better to use partition_text if possible or just wrap in elements
            
            # Improved approach: Use partition_text to handle paragraphs etc if supported
            # or just create Text elements.
            # Let's assume input text is the "document".
            
            elements = [Text(text)]
            
            # Chunk the elements
            chunks = chunk_by_title(
                elements,
                max_characters=1000,
                new_after_n_chars=1500,
                combine_text_under_n_chars=500,
            )

            processed_chunks = []
            base_metadata = metadata or {}
            
            for chunk in chunks:
                chunk_meta = base_metadata.copy()
                chunk_meta.update({
                    "filename": filename,
                    "source": "unstructured_etl_text",
                })
                
                processed_chunks.append({
                    "text": str(chunk),
                    "metadata": chunk_meta
                })
                
            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing text for {filename}: {e}")
            raise
# Singleton
processor = DocumentProcessor()
