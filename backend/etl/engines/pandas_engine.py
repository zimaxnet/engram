"""
Pandas Engine - Class C (Operational Telemetry)
===============================================
System: Engram Context Ecology Platform
Author: Zimax Networks LC

Handles structured data conversion:
- CSV logs
- JSON telemetry
- Parquet files

Converts rows directly to vectors without OCR.
Numbers remain numbers, not text.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Pandas should be available in most environments
try:
    import pandas as pd
    _pandas_available = True
except ImportError:
    pd = None
    _pandas_available = False
    logger.warning("Pandas not installed. Class C processing unavailable.")


class PandasEngine:
    """
    Class C Extraction Engine using Pandas.
    
    Handles operational/telemetry data:
    - CSV files (sensor logs, metrics)
    - JSON files (API responses, configs)
    - Parquet files (analytics data)
    
    Key behaviors:
    - Preserves numeric types for vector math
    - Fast decay (logs expire quickly)
    - Row-level granularity
    """
    
    DECAY_RATE = 0.99  # Logs decay almost instantly
    
    def __init__(self, max_rows: Optional[int] = None):
        """
        Initialize Pandas engine.
        
        Args:
            max_rows: Optional limit on rows to process (for large files)
        """
        self.max_rows = max_rows
    
    @property
    def available(self) -> bool:
        """Check if Pandas is available."""
        return _pandas_available
    
    def process(
        self,
        file_path: str,
        filename: Optional[str] = None,
        decay_rate: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a structured data file.
        
        Args:
            file_path: Path to the data file
            filename: Optional override for the filename in metadata
            decay_rate: Override default decay rate
            
        Returns:
            List of chunks (one per row) with data and metadata
        """
        if not _pandas_available:
            raise RuntimeError("Pandas not available. Install with: pip install pandas")
        
        path = Path(file_path)
        fname = filename or path.name
        ext = path.suffix.lower()
        decay = decay_rate if decay_rate is not None else self.DECAY_RATE
        
        logger.info(f"Pandas: Loading {fname} ({ext})")
        
        # Load based on extension
        df = self._load_dataframe(str(path), ext)
        
        if df is None or df.empty:
            logger.warning(f"Pandas: Empty dataframe from {fname}")
            return []
        
        # Limit rows if configured
        if self.max_rows and len(df) > self.max_rows:
            logger.info(f"Pandas: Limiting to {self.max_rows} rows (was {len(df)})")
            df = df.head(self.max_rows)
        
        # Convert each row to a chunk
        chunks = []
        id_column = self._detect_id_column(df)
        
        for idx, row in df.iterrows():
            # Convert row to JSON string for text field
            row_dict = row.to_dict()
            text_content = json.dumps(row_dict, default=str, ensure_ascii=False)
            
            # Determine entity from ID column or index
            entity = str(row[id_column]) if id_column else f"row_{idx}"
            
            chunks.append({
                "text": text_content,
                "metadata": {
                    "filename": fname,
                    "source": "pandas_class_c",
                    "data_class": "CLASS_C_OPS",
                    "decay_rate": decay,
                    "row_index": int(idx) if isinstance(idx, (int, float)) else str(idx),
                    "entity": entity,
                    "columns": list(df.columns),
                },
                # Preserve structured data for downstream processing
                "structured_data": row_dict,
            })
        
        logger.info(f"Pandas: Converted {len(chunks)} rows from {fname}")
        return chunks
    
    def process_bytes(
        self,
        content: bytes,
        filename: str,
        decay_rate: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process data from bytes.
        
        Args:
            content: Raw bytes of the data file
            filename: Filename for extension detection
            decay_rate: Override default decay rate
            
        Returns:
            List of chunks (one per row)
        """
        import tempfile
        import os
        
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            return self.process(tmp_path, filename=filename, decay_rate=decay_rate)
        finally:
            os.unlink(tmp_path)
    
    def _load_dataframe(self, file_path: str, ext: str):
        """Load dataframe based on file extension."""
        try:
            if ext == '.csv':
                return pd.read_csv(file_path)
            elif ext == '.json':
                # Try records format first, then standard
                try:
                    return pd.read_json(file_path)
                except ValueError:
                    return pd.read_json(file_path, lines=True)
            elif ext == '.parquet':
                return pd.read_parquet(file_path)
            elif ext == '.log':
                # Treat log files as single-column text
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                return pd.DataFrame({'log_line': lines})
            else:
                logger.warning(f"Pandas: Unknown extension {ext}, trying CSV")
                return pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Pandas: Failed to load {file_path}: {e}")
            return None
    
    def _detect_id_column(self, df) -> Optional[str]:
        """Detect likely ID column from dataframe."""
        id_patterns = ['id', 'uuid', 'key', 'name', 'timestamp', 'date']
        
        for col in df.columns:
            col_lower = col.lower()
            for pattern in id_patterns:
                if pattern in col_lower:
                    return col
        
        # Fall back to first column
        return df.columns[0] if len(df.columns) > 0 else None


# Singleton instance
pandas_engine = PandasEngine()
