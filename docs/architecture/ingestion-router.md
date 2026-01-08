# Antigravity Ingestion Router

![Antigravity Ingestion Router Architecture](/docs/architecture/engram-antigravity-ingestion-router.png)

The **Antigravity Ingestion Router** classifies documents by their "Truth Value" and routes them to specialized extraction engines.

## Data Classes

| Class | Name | Engine | Decay Rate | Use Case |
|-------|------|--------|------------|----------|
| **A** | Immutable Truth | Docling | 0.01 | Manuals, specs, safety docs |
| **B** | Ephemeral Chatter | Unstructured | 0.80 | Email, PPT, meeting notes |
| **C** | Operational Telemetry | Pandas | 0.99 | CSV logs, JSON telemetry |

## Quick Start

```python
from backend.etl.antigravity_router import antigravity_router

# Automatic classification and processing
chunks = antigravity_router.ingest("safety_manual.pdf")

# Classification only
data_class, reason = antigravity_router.classify("report.docx")
```

## CLI Testing

```bash
# Classify a file (dry run)
python scripts/test_router.py --file document.pdf --dry-run

# Run automated tests
python scripts/test_router.py --test-mode
```

## Classification Heuristics

### Class A (Docling)

- Extensions: `.pdf`, `.scidoc`
- Keywords: manual, spec, iso, safety, protocol, engineering

### Class B (Unstructured)

- Extensions: `.docx`, `.pptx`, `.eml`, `.msg`, `.html`, `.txt`

### Class C (Pandas)

- Extensions: `.csv`, `.json`, `.parquet`, `.log`

## Metadata Fields

Every chunk includes:

| Field | Type | Description |
|-------|------|-------------|
| `provenance_id` | UUID | Immutable link to source |
| `data_class` | String | Classification result |
| `decay_rate` | Float | Relevance half-life (0-1) |
| `ingest_timestamp` | ISO8601 | When ingested |
| `router_reason` | String | Why this class was chosen |

## Fallback Behavior

If Docling is unavailable (~2GB models), Class A documents automatically fallback to Unstructured with `hi_res` strategy.

## Module Structure

```
backend/etl/
├── antigravity_router.py    # Main router
├── engines/
│   ├── __init__.py
│   ├── docling_engine.py    # Class A
│   ├── unstructured_engine.py # Class B
│   └── pandas_engine.py     # Class C
└── processor.py             # Legacy (deprecated)
```
