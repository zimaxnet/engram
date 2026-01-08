"""
Docling Engine - Class A (Immutable Truth)
==========================================
System: Engram Context Ecology Platform
Author: Zimax Networks LC

Handles high-fidelity extraction from technical documents:
- Engineering Manuals
- Safety Protocols
- ISO Standards
- Scientific Papers

Uses IBM Docling with TableFormer for:
- Table reconstruction
- Multi-column layout preservation
- Bounding-box coordinates for provenance
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy import - Docling has large model dependencies
_docling_available = None
_DocumentConverter = None


def _ensure_docling():
    """Lazily import Docling to avoid loading 2GB models on startup."""
    global _docling_available, _DocumentConverter
    if _docling_available is None:
        try:
            from docling.document_converter import DocumentConverter
            _DocumentConverter = DocumentConverter
            _docling_available = True
            logger.info("Docling engine initialized (TableFormer ready)")
        except ImportError:
            _docling_available = False
            logger.warning(
                "Docling not installed. Class A documents will fallback to Unstructured. "
                "Install with: pip install docling"
            )
    return _docling_available


class DoclingEngine:
    """
    Class A Extraction Engine using IBM Docling.
    
    Extracts structural elements with full provenance:
    - Tables with TableFormer reconstruction
    - Headings, paragraphs, lists
    - Page numbers and bounding boxes
    """
    
    DECAY_RATE = 0.01  # Manuals are eternal
    
    def __init__(self):
        self._converter = None
    
    def _get_converter(self):
        """Get or create the Docling converter (lazy initialization)."""
        if self._converter is None and _ensure_docling():
            self._converter = _DocumentConverter()
        return self._converter
    
    @property
    def available(self) -> bool:
        """Check if Docling is available."""
        return _ensure_docling()
    
    def process(
        self,
        file_path: str,
        filename: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a document using Docling.
        
        Args:
            file_path: Path to the document file
            filename: Optional override for the filename in metadata
            
        Returns:
            List of chunks with text, metadata, and provenance
        """
        converter = self._get_converter()
        if converter is None:
            raise RuntimeError(
                "Docling not available. Install with: pip install docling"
            )
        
        path = Path(file_path)
        fname = filename or path.name
        
        logger.info(f"Docling: Processing {fname} with TableFormer...")
        
        result = converter.convert(str(path))
        doc = result.document
        
        chunks = []
        for item, level in doc.iterate_items():
            text_content = getattr(item, 'text', '')
            if not text_content or not text_content.strip():
                continue
            
            # Extract provenance (page, bounding box)
            page_no = None
            bbox = None
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0]
                page_no = getattr(prov, 'page_no', None)
                if hasattr(prov, 'bbox') and prov.bbox:
                    bbox = prov.bbox.as_tuple() if hasattr(prov.bbox, 'as_tuple') else None
            
            chunks.append({
                "text": text_content,
                "metadata": {
                    "filename": fname,
                    "source": "docling_class_a",
                    "data_class": "CLASS_A_TRUTH",
                    "decay_rate": self.DECAY_RATE,
                    "page_number": page_no,
                    "bounding_box": list(bbox) if bbox else None,
                    "level": level,
                    "element_type": type(item).__name__,
                }
            })
        
        logger.info(f"Docling: Extracted {len(chunks)} elements from {fname}")
        return chunks
    
    def process_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> List[Dict[str, Any]]:
        """
        Process document bytes (requires temp file for Docling).
        
        Args:
            content: Raw bytes of the document
            filename: Filename for the document
            
        Returns:
            List of chunks with text and metadata
        """
        import tempfile
        import os
        
        # Docling requires file path, not bytes
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            return self.process(tmp_path, filename=filename)
        finally:
            os.unlink(tmp_path)


# Singleton instance
docling_engine = DoclingEngine()
