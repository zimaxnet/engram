# Knowledge Graph Implementation

## Overview

The Engram Knowledge Graph provides a semantic layer over the episodic memory and documentation, linking entities (pages, topics, concepts) in a directed graph structure.

## Architecture

### 1. Storage Layer

- **Technology**: NetworkX (In-Memory Python Graph Library).
- **Persistence**: JSON file storage at `docs/knowledge_graph.json`.
- **Reasoning**: Chosen for simplicity and ease of deployment (no massive DB operational overhead) while providing powerful graph algorithms.
- **Failover**: Kuzu was initially planned but replaced due to build environment constraints.

### 2. Backend (Python/FastAPI)

- **Client**: `SimpleGraphClient` (Singleton) in `backend/core/graph_client.py`.
- **API**: Exposed via `backend/api/routers/graph.py`:
  - `GET /api/v1/graph/search?query=...`: Fuzzy search for nodes.
  - `GET /api/v1/graph/dump`: Returns full graph layout (nodes/links).

### 3. Ingestion

- **Script**: `scripts/ingest_wiki.py`.
- **Process**:
  1. Fetches Wiki pages.
  2. Extracts metadata (slug, title, topics).
  3. Creates `Page` nodes and `Topic` edges in the graph.
  4. Persists to `docs/knowledge_graph.json`.

### 4. Frontend (React)

- **Library**: `react-force-graph-2d`.
- **Component**: `KnowledgeGraph.tsx`.
- **Features**:
  - Interactive force-directed layout.
  - Zoom/Pan/Drag interactions.
  - Dynamic node sizing and coloring.
  - Real-time data fetching from API.

## Future Roadmap

- **LLM Extraction**: Use Gemini/Claude to extract semantic triplets (Subject-Predicate-Object) from page content during ingestion.
- **Interactive Search**: Click-to-query context in the UI.
- **Vector Integration**: Link graph nodes to Zep vector memory for hybrid search.
