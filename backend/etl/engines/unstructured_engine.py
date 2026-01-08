"""
Unstructured Engine - Class B (Ephemeral Chatter)
=================================================
System: Engram Context Ecology Platform
Author: Zimax Networks LC

Handles semantic chunking from narrative documents:
- Emails (.eml, .msg)
- Presentations (.pptx)
- Word documents (.docx)
- HTML/Web content
- Meeting transcripts

Uses Unstructured.io for:
- Content partitioning by element type
- Semantic chunking by title/headers
- Metadata extraction
"""

import logging
import io
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy import for optional dependency
_unstructured_available = None
_partition = None
_chunk_by_title = None


def _ensure_unstructured():
    """Lazily import Unstructured."""
    global _unstructured_available, _partition, _chunk_by_title
    if _unstructured_available is None:
        try:
            from unstructured.partition.auto import partition
            from unstructured.chunking.title import chunk_by_title
            _partition = partition
            _chunk_by_title = chunk_by_title
            _unstructured_available = True
            logger.debug("Unstructured engine initialized")
        except ImportError:
            _unstructured_available = False
            logger.warning(
                "Unstructured not installed. Class B processing unavailable. "
                "Install with: pip install 'unstructured[all-docs]'"
            )
    return _unstructured_available


class UnstructuredEngine:
    """
    Class B Extraction Engine using Unstructured.io.
    
    Extracts narrative content with semantic chunking:
    - Chunks by title/header boundaries
    - Preserves element types (Title, NarrativeText, ListItem)
    - Optimized for messy/unstructured content
    """
    
    DECAY_RATE = 0.80  # Ephemeral content decays fast
    
    def __init__(
        self,
        max_characters: int = 1000,
        new_after_n_chars: int = 1500,
        combine_text_under_n_chars: int = 500,
    ):
        self.max_characters = max_characters
        self.new_after_n_chars = new_after_n_chars
        self.combine_text_under_n_chars = combine_text_under_n_chars
    
    @property
    def available(self) -> bool:
        """Check if Unstructured is available."""
        return _ensure_unstructured()
    
    def process(
        self,
        file_path: str,
        filename: Optional[str] = None,
        strategy: str = "hi_res",
        decay_rate: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a document using Unstructured.
        
        Args:
            file_path: Path to the document file
            filename: Optional override for the filename in metadata
            strategy: 'fast' or 'hi_res' (OCR)
            decay_rate: Override default decay rate
            
        Returns:
            List of chunks with text and metadata
        """
        if not _ensure_unstructured():
            raise RuntimeError(
                "Unstructured not available. Install with: pip install 'unstructured[all-docs]'"
            )
        
        fname = filename or file_path.split("/")[-1]
        decay = decay_rate if decay_rate is not None else self.DECAY_RATE
        
        logger.info(f"Unstructured: Processing {fname} with strategy={strategy}")
        
        elements = _partition(filename=file_path, strategy=strategy)
        
        chunks = _chunk_by_title(
            elements,
            max_characters=self.max_characters,
            new_after_n_chars=self.new_after_n_chars,
            combine_text_under_n_chars=self.combine_text_under_n_chars,
        )
        
        result = []
        for chunk in chunks:
            text_content = str(chunk)
            if len(text_content) < 10:
                continue
            
            page_number = None
            filetype = None
            if hasattr(chunk, 'metadata'):
                page_number = getattr(chunk.metadata, 'page_number', None)
                filetype = getattr(chunk.metadata, 'filetype', None)
            
            result.append({
                "text": text_content,
                "metadata": {
                    "filename": fname,
                    "source": "unstructured_class_b",
                    "data_class": "CLASS_B_CHATTER",
                    "decay_rate": decay,
                    "page_number": page_number,
                    "filetype": filetype,
                    "element_type": type(chunk).__name__,
                }
            })
        
        logger.info(f"Unstructured: Extracted {len(result)} chunks from {fname}")
        return result
    
    def process_bytes(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        strategy: str = "hi_res",
        decay_rate: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process document bytes directly.
        
        Args:
            content: Raw bytes of the document
            filename: Filename for the document
            content_type: MIME type hint
            strategy: 'fast' or 'hi_res'
            decay_rate: Override default decay rate
            
        Returns:
            List of chunks with text and metadata
        """
        if not _ensure_unstructured():
            raise RuntimeError("Unstructured not available.")
        
        fname = filename
        decay = decay_rate if decay_rate is not None else self.DECAY_RATE
        
        logger.info(f"Unstructured: Processing {fname} (bytes) with strategy={strategy}")
        
        file_obj = io.BytesIO(content)
        
        elements = _partition(
            file=file_obj,
            file_filename=filename,
            content_type=content_type,
            strategy=strategy,
        )
        
        chunks = _chunk_by_title(
            elements,
            max_characters=self.max_characters,
            new_after_n_chars=self.new_after_n_chars,
            combine_text_under_n_chars=self.combine_text_under_n_chars,
        )
        
        result = []
        for chunk in chunks:
            text_content = str(chunk)
            if len(text_content) < 10:
                continue
            
            page_number = None
            filetype = None
            if hasattr(chunk, 'metadata'):
                page_number = getattr(chunk.metadata, 'page_number', None)
                filetype = getattr(chunk.metadata, 'filetype', None)
            
            result.append({
                "text": text_content,
                "metadata": {
                    "filename": fname,
                    "source": "unstructured_class_b",
                    "data_class": "CLASS_B_CHATTER",
                    "decay_rate": decay,
                    "page_number": page_number,
                    "filetype": filetype,
                    "element_type": type(chunk).__name__,
                }
            })
        
        logger.info(f"Unstructured: Extracted {len(result)} chunks from {fname}")
        return result


# Singleton instance
unstructured_engine = UnstructuredEngine()
