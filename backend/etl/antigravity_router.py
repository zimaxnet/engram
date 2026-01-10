"""
Antigravity Ingestion Router
============================
System: Engram Context Ecology Platform
Author: Zimax Networks LC

MISSION:
Defy data gravity by routing ingestion based on "Truth Value".
- Class A (Immutable Truth) -> Docling (IBM) for structural fidelity.
- Class B (Ephemeral Chatter) -> Unstructured.io for semantic chunking.
- Class C (Operational Telemetry) -> Pandas for row-to-vector conversion.

MANDATORY METADATA:
- provenance_id: Immutable source link.
- decay_rate: Relevance half-life.
- data_class: Classification for downstream processing.

Usage:
    from backend.etl.antigravity_router import antigravity_router
    
    # Route and process a file
    chunks = antigravity_router.ingest("safety_manual.pdf")
    
    # Just get classification (no processing)
    data_class = antigravity_router.classify("meeting_notes.docx")
"""

import logging
import os
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class DataClass(Enum):
    """Data classification for Engram ingestion routing."""
    CLASS_A_TRUTH = "immutable_truth"       # Manuals, Specs, Safety (Docling)
    CLASS_B_CHATTER = "ephemeral_stream"    # Email, PPT, Slack (Unstructured)
    CLASS_C_OPS = "operational_pulse"       # Logs, CSV (Pandas)


# File extension mappings
CLASS_A_EXTENSIONS = {'.pdf', '.scidoc'}
CLASS_B_EXTENSIONS = {'.pptx', '.docx', '.doc', '.eml', '.msg', '.html', '.htm', '.txt', '.md', '.rtf'}
CLASS_C_EXTENSIONS = {'.csv', '.parquet', '.json', '.log', '.jsonl', '.ndjson'}

# Keywords that indicate technical/immutable content (for PDF heuristics)
TRUTH_KEYWORDS = {
    'manual', 'spec', 'specification', 'standard', 'iso', 'safety',
    'protocol', 'procedure', 'guideline', 'engineering', 'technical',
    'datasheet', 'schematic', 'regulation', 'compliance', 'certification'
}


class AntigravityRouter:
    """
    Routes documents to the appropriate extraction engine based on Truth Value.
    
    The router classifies documents and delegates to:
    - DoclingEngine: High-fidelity extraction (tables, layouts, bounding boxes)
    - UnstructuredEngine: Semantic chunking (narrative content)
    - PandasEngine: Structured data conversion (rows to vectors)
    """
    
    def __init__(self, fallback_to_unstructured: bool = True):
        """
        Initialize the router.
        
        Args:
            fallback_to_unstructured: If True, Class A files fallback to
                                      Unstructured when Docling is unavailable.
        """
        self.fallback_to_unstructured = fallback_to_unstructured
        self._engines_initialized = False
        self._docling = None
        self._unstructured = None
        self._pandas = None
    
    def _init_engines(self):
        """Lazy initialization of engines."""
        if self._engines_initialized:
            return
        
        try:
            from backend.etl.engines.docling_engine import docling_engine
            self._docling = docling_engine
        except ImportError:
            logger.warning("Docling engine not available")
        
        try:
            from backend.etl.engines.unstructured_engine import unstructured_engine
            self._unstructured = unstructured_engine
        except ImportError:
            logger.warning("Unstructured engine not available")
        
        try:
            from backend.etl.engines.pandas_engine import pandas_engine
            self._pandas = pandas_engine
        except ImportError:
            logger.warning("Pandas engine not available")
        
        self._engines_initialized = True
    
    def classify(self, file_path: str) -> Tuple[DataClass, str]:
        """
        Classify a file into a Data Class.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (DataClass, reason)
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        filename = path.name.lower()
        
        # CLASS C: Operational/Structured Data (highest priority for speed)
        if ext in CLASS_C_EXTENSIONS:
            return DataClass.CLASS_C_OPS, f"Extension {ext} -> Pandas"
        
        # CLASS A: Immutable Truth (PDFs with technical indicators)
        if ext in CLASS_A_EXTENSIONS:
            if self._is_technical_document(filename, file_path):
                return DataClass.CLASS_A_TRUTH, f"Extension {ext} + technical keywords -> Docling"
            # Default PDFs to Class A for industrial context
            return DataClass.CLASS_A_TRUTH, f"Extension {ext} (default) -> Docling"
        
        # CLASS B: Ephemeral Chatter
        if ext in CLASS_B_EXTENSIONS:
            return DataClass.CLASS_B_CHATTER, f"Extension {ext} -> Unstructured"
        
        # Unknown: Default to Unstructured (fast strategy)
        return DataClass.CLASS_B_CHATTER, f"Unknown extension {ext} -> Unstructured (fallback)"
    
    def _is_technical_document(self, filename: str, file_path: str) -> bool:
        """
        Determine if a document is likely technical/immutable.
        
        Uses filename heuristics. Could be extended with:
        - First-page text analysis
        - Metadata extraction
        - ML classification
        """
        filename_lower = filename.lower()
        
        for keyword in TRUTH_KEYWORDS:
            if keyword in filename_lower:
                return True
        
        return False
    
    def ingest(
        self,
        file_path: str,
        filename: Optional[str] = None,
        force_class: Optional[DataClass] = None,
    ) -> List[Dict[str, Any]]:
        """
        Route a file to the appropriate engine and process it.
        
        Args:
            file_path: Path to the document
            filename: Optional display name for metadata
            force_class: Override automatic classification
            
        Returns:
            List of chunks with text and metadata
        """
        self._init_engines()
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        fname = filename or path.name
        
        # Classify or use forced class
        if force_class:
            data_class = force_class
            reason = f"Forced: {force_class.name}"
        else:
            data_class, reason = self.classify(file_path)
        
        logger.info(f"Antigravity Router: {fname} -> {data_class.name} ({reason})")
        
        # Route to appropriate engine
        chunks = self._execute_engine(file_path, fname, data_class)
        
        # Add provenance to all chunks
        provenance_id = str(uuid.uuid4())
        ingest_timestamp = datetime.now(UTC).isoformat()
        
        for chunk in chunks:
            chunk["metadata"]["provenance_id"] = provenance_id
            chunk["metadata"]["ingest_timestamp"] = ingest_timestamp
            chunk["metadata"]["router_reason"] = reason
        
        return chunks
    
    def ingest_bytes(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        force_class: Optional[DataClass] = None,
    ) -> List[Dict[str, Any]]:
        """
        Route document bytes to the appropriate engine.
        
        Args:
            content: Raw bytes of the document
            filename: Filename for classification and metadata
            content_type: MIME type hint
            force_class: Override automatic classification
            
        Returns:
            List of chunks with text and metadata
        """
        self._init_engines()
        
        # Classify based on filename
        if force_class:
            data_class = force_class
            reason = f"Forced: {force_class.name}"
        else:
            # Create a fake path for classification
            data_class, reason = self.classify(filename)
        
        logger.info(f"Antigravity Router: {filename} (bytes) -> {data_class.name} ({reason})")
        
        # Route to appropriate engine
        chunks = self._execute_engine_bytes(content, filename, content_type, data_class)
        
        # Add provenance
        provenance_id = str(uuid.uuid4())
        ingest_timestamp = datetime.now(UTC).isoformat()
        
        for chunk in chunks:
            chunk["metadata"]["provenance_id"] = provenance_id
            chunk["metadata"]["ingest_timestamp"] = ingest_timestamp
            chunk["metadata"]["router_reason"] = reason
        
        return chunks
    
    def _execute_engine(
        self,
        file_path: str,
        filename: str,
        data_class: DataClass,
    ) -> List[Dict[str, Any]]:
        """Execute the appropriate engine for file path."""
        
        if data_class == DataClass.CLASS_A_TRUTH:
            if self._docling and self._docling.available:
                return self._docling.process(file_path, filename)
            elif self.fallback_to_unstructured and self._unstructured:
                logger.warning(f"Docling unavailable, falling back to Unstructured for {filename}")
                return self._unstructured.process(file_path, filename, strategy="hi_res")
            else:
                raise RuntimeError("No engine available for Class A documents")
        
        elif data_class == DataClass.CLASS_B_CHATTER:
            if self._unstructured and self._unstructured.available:
                return self._unstructured.process(file_path, filename, strategy="hi_res")
            else:
                raise RuntimeError("Unstructured not available for Class B documents")
        
        elif data_class == DataClass.CLASS_C_OPS:
            if self._pandas and self._pandas.available:
                return self._pandas.process(file_path, filename)
            else:
                raise RuntimeError("Pandas not available for Class C documents")
        
        # Should never reach here
        raise ValueError(f"Unknown data class: {data_class}")
    
    def _execute_engine_bytes(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str],
        data_class: DataClass,
    ) -> List[Dict[str, Any]]:
        """Execute the appropriate engine for bytes."""
        
        if data_class == DataClass.CLASS_A_TRUTH:
            if self._docling and self._docling.available:
                return self._docling.process_bytes(content, filename)
            elif self.fallback_to_unstructured and self._unstructured:
                logger.warning(f"Docling unavailable, falling back to Unstructured for {filename}")
                return self._unstructured.process_bytes(content, filename, content_type, strategy="hi_res")
            else:
                raise RuntimeError("No engine available for Class A documents")
        
        elif data_class == DataClass.CLASS_B_CHATTER:
            if self._unstructured and self._unstructured.available:
                return self._unstructured.process_bytes(content, filename, content_type, strategy="hi_res")
            else:
                raise RuntimeError("Unstructured not available for Class B documents")
        
        elif data_class == DataClass.CLASS_C_OPS:
            if self._pandas and self._pandas.available:
                return self._pandas.process_bytes(content, filename)
            else:
                raise RuntimeError("Pandas not available for Class C documents")
        
        raise ValueError(f"Unknown data class: {data_class}")


# Singleton instance
antigravity_router = AntigravityRouter()


# --- Convenience Functions (matches pseudocode) ---

def is_technical_manual(file_path: str) -> bool:
    """Check if a file is a technical manual (for pseudocode compatibility)."""
    return antigravity_router._is_technical_document(
        Path(file_path).name.lower(),
        file_path
    )


def ingest_with_docling(file_path: str, mode: str = "table_former") -> List[Dict[str, Any]]:
    """Ingest using Docling (for pseudocode compatibility)."""
    return antigravity_router.ingest(file_path, force_class=DataClass.CLASS_A_TRUTH)


def ingest_with_unstructured(file_path: str, strategy: str = "hi_res") -> List[Dict[str, Any]]:
    """Ingest using Unstructured (for pseudocode compatibility)."""
    return antigravity_router.ingest(file_path, force_class=DataClass.CLASS_B_CHATTER)


def ingest_structured_data(file_path: str) -> List[Dict[str, Any]]:
    """Ingest using Pandas (for pseudocode compatibility)."""
    return antigravity_router.ingest(file_path, force_class=DataClass.CLASS_C_OPS)
