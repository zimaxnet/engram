"""
Antigravity Engines - Class-Specific Extraction Modules
========================================================
- docling_engine: Class A (Immutable Truth)
- unstructured_engine: Class B (Ephemeral Chatter)
- pandas_engine: Class C (Operational Telemetry)
"""

from .docling_engine import DoclingEngine
from .unstructured_engine import UnstructuredEngine
from .pandas_engine import PandasEngine

__all__ = ["DoclingEngine", "UnstructuredEngine", "PandasEngine"]
