# Graph Knowledge & Tri-Search: Engram's Unique Differentiator

## Overview

Engram's Graph Knowledge (Gk) is a unique differentiator in the AI Periodic Table framework. It represents the critical third layer of Engram's emergent tri-search capability, enabling relationship-based reasoning and multi-hop traversal.

## Tri-Search Architecture

Engram's memory retrieval uses three complementary search layers combined via Reciprocal Rank Fusion (RRF):

1. **Keyword Search (BM25/Lexical)**: Exact phrase matching, acronym lookup, terminology search
   - Storage: Zep sessions with chunked messages
   - Enables: Exact term matching, acronym resolution, technical term lookup

2. **Vector Search (Semantic)**: Conceptual similarity, paraphrase matching, meaning-based retrieval
   - Storage: memory_embeddings table (pgvector)
   - Embedding Model: text-embedding-3-small (1536 dimensions)
   - Enables: Conceptual similarity, paraphrase detection, context-aware retrieval

3. **Graph Search (Knowledge Graph)**: Relationship traversal, entity connections, multi-hop reasoning
   - Storage: Zep Temporal Knowledge Graph
   - Enables: Entity relationship discovery, multi-hop reasoning, temporal fact tracking, cross-session knowledge assembly

## Graph Knowledge Structure

### Node Types

- **Fact** (Cyan #00d4ff): Semantic facts extracted from conversations
- **Entity** (Purple #a855f7): People, projects, concepts
- **Memory** (Green #10b981): Episodic memory (conversation sessions)
- **Topic** (Amber #f59e0b): Conversation topics/themes
- **Metadata** (Gray #6b7280): Source, filename, tenant tags

### Edge Types

- `concerns`: Episode relates to topic
- `source`: Fact comes from source
- `related_to`: Entities are related
- `mentions`: Content mentions entity

## Knowledge Graph Interface

**URL**: https://engram.work/memory/graph

**Features**:
- Interactive force-directed graph visualization
- Search and filter by query, node type, and degree
- Statistics dashboard (total nodes, edges, average degree, node type breakdown)
- Node details panel (content, metadata, connections)
- Tri-search context explanation

## API Endpoint

```
GET /api/memory/graph?query=<search_term>
```

Returns graph nodes, edges, and statistics including:
- Total nodes and edges
- Node types breakdown
- Average and maximum degree
- Filtered by query if provided

## Use Cases

1. **Entity Discovery**: Find who worked on a project by traversing graph relationships
2. **Project Timeline**: View chronological project history via episode traversal
3. **Knowledge Gap Analysis**: Identify isolated nodes (low degree) needing more context
4. **Multi-Hop Reasoning**: Answer complex queries requiring multiple relationship hops

## How It Works

Graph Knowledge is built automatically from:
- Conversations: Entities, facts, and topics extracted from agent conversations
- Documents: Entities and facts from ingested documents
- Episodes: Session summaries become memory nodes with topic links

Users can also manually add facts via POST /api/memory/facts

## Observability

**Available**:
- Graph structure visualization
- Node details (content, metadata, connections)
- Statistics (total nodes, edges, degree metrics)
- Search transparency (which nodes match query)

**Planned**:
- Tri-search breakdown (which layer contributed each result)
- Retrieval path visualization
- Graph analytics (centrality, community detection)
- Time slider for temporal graph views

## Technical Implementation

- Backend: Zep Cloud Temporal Knowledge Graph, entity extraction, fact storage
- Frontend: react-force-graph-2d visualization, interactive filtering
- Data Flow: User query → GET /api/memory/graph → _build_graph() → Zep APIs → Graph + Stats → Visualization

## Related Documentation

- Full guide: docs/features/memory/graph-knowledge-tri-search.md
- AI Periodic Table: docs/wiki/ai-periodic-table.md
- Roadmap: docs/ai-periodic-table-roadmap.md

