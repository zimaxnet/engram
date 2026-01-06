---
layout: default
title: Graph Knowledge & Tri-Search
parent: Memory
nav_order: 1
---

# Graph Knowledge & Tri-Search: Engram's Unique Differentiator

> **The critical third layer of Engram's emergent tri-search capability, enabling relationship-based reasoning and multi-hop traversal.**

---

## Executive Summary

Engram's **Graph Knowledge (Gk)** is a unique differentiator in the AI Periodic Table framework. While most platforms rely on static RAG (retrieve → augment → generate), Engram uses **dynamic Graph Knowledge orchestration** that enables:

- **Relationship-based reasoning**: Understand how entities connect
- **Multi-hop traversal**: Follow connections across the knowledge graph
- **Temporal awareness**: Knowledge evolves over time with timestamps
- **Cross-session learning**: Knowledge compounds automatically across conversations

This document explains how Graph Knowledge works as part of Engram's **tri-search** capability and how to use the Knowledge Graph visualization interface.

---

## Tri-Search Architecture

Engram's memory retrieval uses **three complementary search layers** combined via Reciprocal Rank Fusion (RRF):

### 1. Keyword Search (BM25/Lexical)

**Purpose**: Exact phrase matching, acronym lookup, terminology search

**Storage**: Zep sessions with chunked messages  
**Session Pattern**: `doc-upload-{uuid}`, `doc-wiki-*`, `sess-*`  
**Enables**: 
- Exact term matching
- Acronym resolution
- Technical term lookup
- Document title/topic matching

**Example**: Searching for "API" finds exact mentions of "API" in documents and conversations.

### 2. Vector Search (Semantic)

**Purpose**: Conceptual similarity, paraphrase matching, meaning-based retrieval

**Storage**: `memory_embeddings` table (pgvector)  
**Embedding Model**: `text-embedding-3-small` (1536 dimensions)  
**Enables**:
- Conceptual similarity (e.g., "API" matches "application programming interface")
- Paraphrase detection
- Cross-language understanding
- Context-aware retrieval

**Example**: Searching for "user authentication" finds content about "login", "credentials", "sign-in", etc.

### 3. Graph Search (Knowledge Graph) ⭐ **Unique**

**Purpose**: Relationship traversal, entity connections, multi-hop reasoning

**Storage**: Zep Temporal Knowledge Graph  
**Enables**:
- Entity relationship discovery
- Multi-hop reasoning (A → B → C)
- Temporal fact tracking
- Cross-session knowledge assembly
- Semantic routing based on relationships

**Example**: Searching for "Elena" finds not just mentions, but also related projects, conversations, and facts connected to Elena.

---

## How Tri-Search Works Together

### Reciprocal Rank Fusion (RRF)

Results from all three layers are combined using RRF:

```
RRF Score = Σ (1 / (k + rank_i))
```

Where:
- `k = 60` (standard RRF constant)
- `rank_i` = rank of result in layer i (keyword, vector, or graph)

**Benefits**:
- Combines strengths of all three methods
- Handles cases where one method fails
- Provides comprehensive coverage
- Balances precision and recall

### Example Query Flow

**Query**: "What did Elena say about the authentication system?"

1. **Keyword Search**: Finds exact mentions of "Elena" + "authentication"
2. **Vector Search**: Finds semantically similar content about "user login" and "Elena"
3. **Graph Search**: Traverses relationships:
   - Finds "Elena" entity node
   - Follows edges to related conversations
   - Discovers "authentication" topic node
   - Retrieves connected facts and episodes

4. **RRF Fusion**: Combines results, ranking by relevance across all three layers

---

## Graph Knowledge Structure

### Node Types

| Type | Description | Color | Example |
|------|-------------|-------|---------|
| **Fact** | Semantic facts extracted from conversations | Cyan (`#00d4ff`) | "Elena is a business analyst" |
| **Entity** | People, projects, concepts | Purple (`#a855f7`) | "Elena Vasquez", "Project Alpha" |
| **Memory** | Episodic memory (conversation sessions) | Green (`#10b981`) | "Session: 2025-01-15 chat" |
| **Topic** | Conversation topics/themes | Amber (`#f59e0b`) | "authentication", "requirements" |
| **Metadata** | Source, filename, tenant tags | Gray (`#6b7280`) | "source:wiki", "tenant:acme" |

### Edge Types

| Label | Meaning | Example |
|-------|---------|---------|
| `concerns` | Episode relates to topic | Episode → Topic |
| `source` | Fact comes from source | Fact → Metadata |
| `related_to` | Entities are related | Entity → Entity |
| `mentions` | Content mentions entity | Memory → Entity |

### Graph Properties

- **Degree**: Number of connections a node has
  - High degree = central/hub node (important)
  - Low degree = peripheral node (specialized)
- **Weight**: Strength of relationship (currently 1.0 for all edges)
- **Temporal**: Facts have timestamps, enabling time-aware queries

---

## Using the Knowledge Graph Interface

### Access

Navigate to: **Memory → Gk (Graph Knowledge)**

URL: `https://engram.work/memory/graph`

### Features

#### 1. **Search & Filter**

- **Query Search**: Enter a search term to filter facts and episodes
  - Filters by content and topics
  - Updates graph in real-time
  
- **Node Type Filter**: Filter by node type (Fact, Entity, Memory, Topic, Metadata)
  
- **Min Degree Filter**: Show only nodes with N+ connections (filters out isolated nodes)

#### 2. **Visualization**

- **Force-Directed Layout**: Nodes positioned by connections
  - Connected nodes cluster together
  - Central nodes (high degree) are more prominent
  
- **Node Sizing**: Node size reflects degree (more connections = larger)
  
- **Color Coding**: Each node type has a distinct color
  
- **Interactive**:
  - Click node to select and view details
  - Hover to highlight
  - Drag to reposition (locks position)
  - Zoom and pan

#### 3. **Statistics Panel**

Shows:
- Total nodes and edges
- Average degree (connections per node)
- Maximum degree (most connected node)
- Breakdown by node type

#### 4. **Node Details Panel**

When a node is selected:
- **Content**: Full text/content of the node
- **Type**: Node type with color badge
- **Degree**: Number of connections
- **Metadata**: Source, timestamp, agent_id, etc.
- **Connected Nodes**: List of directly connected nodes (clickable)

#### 5. **Tri-Search Context Panel**

Explains:
- How Graph Knowledge fits into tri-search
- Relationship to Keyword and Vector search
- RRF fusion methodology

---

## Graph Knowledge API

### Endpoint

```
GET /api/v1/memory/graph?query=<search_term>
```

### Transparency Endpoints

```
GET /api/v1/memory/environments
```

Used by the UI to display:
- Active Zep URL (where memory is currently retrieved from)
- Known environment presets (local / azure / staging)

### Response

```json
{
  "nodes": [
    {
      "id": "fact-123",
      "content": "Elena is a business analyst",
      "node_type": "fact",
      "degree": 5,
      "metadata": {
        "source": "conversation",
        "timestamp": "2025-01-15T10:30:00Z"
      }
    }
  ],
  "edges": [
    {
      "id": "edge-123-456",
      "source": "fact-123",
      "target": "entity-elena",
      "label": "mentions",
      "weight": 1.0
    }
  ],
  "stats": {
    "total_nodes": 150,
    "total_edges": 200,
    "node_types": {
      "fact": 50,
      "entity": 30,
      "memory": 40,
      "topic": 20,
      "meta": 10
    },
    "avg_degree": 2.67,
    "max_degree": 15
  }
}
```

### Query Parameters

- `query` (optional): Filter facts and episodes by content/topics

---

## How Graph Knowledge is Built

### Automatic Extraction

Graph Knowledge is built automatically from:

1. **Conversations**: 
   - Entities extracted from agent conversations
   - Facts derived from statements
   - Topics identified from summaries
   
2. **Documents**:
   - Entities extracted during ingestion
   - Facts from document content
   - Metadata tags (source, filename, tenant)
   
3. **Episodes**:
   - Session summaries become memory nodes
   - Topics link to episodes
   - Agent IDs tracked

### Manual Addition

Users can manually add facts via:

```
POST /api/v1/memory/facts
{
  "content": "Custom fact text",
  "fact_type": "custom",
  "confidence": 1.0,
  "metadata": {}
}
```

---

## Use Cases

### 1. **Entity Discovery**

**Scenario**: "Who worked on the authentication project?"

**Graph Traversal**:
1. Find "authentication" topic node
2. Follow edges to related episodes
3. Extract agent_id from episode metadata
4. Find entities connected to those episodes

**Result**: List of people/agents who discussed authentication

### 2. **Project Timeline**

**Scenario**: "What happened with Project Alpha over time?"

**Graph Traversal**:
1. Find "Project Alpha" entity node
2. Follow edges to all connected episodes (sorted by timestamp)
3. Extract summaries and facts from each episode

**Result**: Chronological project history

### 3. **Knowledge Gap Analysis**

**Scenario**: "What topics are isolated (not well-connected)?"

**Graph Analysis**:
1. Find nodes with degree < 2
2. Identify node types (likely topics or entities)
3. Flag as potential knowledge gaps

**Result**: List of topics that need more context/connections

### 4. **Multi-Hop Reasoning**

**Scenario**: "What did Elena say about topics related to security?"

**Graph Traversal**:
1. Find "Elena" entity node
2. Follow edges to episodes where Elena participated
3. From those episodes, follow edges to topics
4. Filter topics containing "security"
5. Retrieve facts from security-related episodes

**Result**: Elena's statements about security topics (even if she didn't explicitly mention "security")

---

## Observability & Transparency

### What You Can See

1. **Graph Structure**: Visual representation of knowledge relationships
2. **Node Details**: Full content, metadata, connections
3. **Statistics**: Quantitative metrics about graph health
4. **Search Transparency**: See which nodes match your query
5. **Function Calls (Fc)**: The UI shows the exact API calls and request timing
6. **Environment Metadata**: Which environment and Zep URL are active

### What You Can't See (Yet)

- **Tri-Search Breakdown**: Which layer (keyword/vector/graph) contributed each result
- **RRF Scores**: Individual scores from each layer
- **Retrieval Path**: Exact traversal path for multi-hop queries
- **Confidence Scores**: How certain the system is about relationships

**Roadmap**: These features are planned for future releases.

---

## Best Practices

### 1. **Start Broad, Then Narrow**

- Begin with no query to see full graph
- Use query to focus on specific topics
- Use filters to isolate node types

### 2. **Explore High-Degree Nodes**

- High-degree nodes are knowledge hubs
- Click to see what they connect to
- Often reveal important concepts

### 3. **Check Isolated Nodes**

- Low-degree nodes may indicate:
  - New topics (recently added)
  - Knowledge gaps (needs more context)
  - Specialized information

### 4. **Use Metadata**

- Check node metadata for:
  - Source (wiki, document, conversation)
  - Timestamp (when knowledge was added)
  - Agent ID (who generated it)

### 5. **Combine with Other Views**

- **Search Page**: See tri-search results in list format
- **Episodes Page**: View conversation history
- **Graph Page**: Understand relationships

---

## Technical Implementation

### Backend

- **Zep Cloud**: Temporal Knowledge Graph storage
- **Entity Extraction**: Automatic via Zep
- **Fact Storage**: User-scoped facts API
- **Graph Building**: `_build_graph()` in `backend/api/routers/memory.py`

### Frontend

- **Visualization**: `react-force-graph-2d`
- **Component**: `frontend/src/pages/Memory/KnowledgeGraph.tsx`
- **API Client**: `getMemoryGraph()` in `frontend/src/services/api.ts`

### Data Flow

```
User Query
    ↓
GET /api/v1/memory/graph?query=...
    ↓
_build_graph(user_id, query)
    ↓
1. Get Facts (Zep Cloud API)
2. Get Episodes (Zep Sessions API)
3. Build Topic Nodes
4. Create Metadata Edges
5. Calculate Statistics
    ↓
Return Graph + Stats
    ↓
Frontend Visualization

---

## Architectural Diagram (Gk in Tri-Search)

```mermaid
flowchart TB
  U[User Query] --> FE[Frontend: /memory/search + /memory/graph]
  FE -->|Fc: GET /api/v1/memory/search| API1[Memory API]
  FE -->|Fc: GET /api/v1/memory/graph| API2[Memory API]
  FE -->|Fc: GET /api/v1/memory/environments| API3[Memory API]

  API1 --> RRF[Reciprocal Rank Fusion]
  API2 --> GK[Graph Knowledge (Gk)]

  RRF --> K[Keyword Search\n(Zep sessions + metadata)]
  RRF --> V[Vector Search\n(pgvector embeddings)]
  RRF --> GK

  GK --> Z[Zep Knowledge Graph\n(facts, entities, edges)]
  K --> ZS[Zep Sessions API\n(episodic + keyword)]
  V --> PG[(Postgres + pgvector)]

  Z --> OUT[Ranked context + provenance]
  ZS --> OUT
  PG --> OUT
```
```

---

## Roadmap

### Planned Enhancements

- [ ] **Tri-Search Breakdown**: Show which layer contributed each result
- [ ] **Retrieval Path Visualization**: Show traversal path for multi-hop queries
- [ ] **Graph Analytics**: Centrality metrics, community detection
- [ ] **Time Slider**: View graph at different time points
- [ ] **Export**: Download graph as JSON/GraphML
- [ ] **Manual Editing**: Add/edit/delete nodes and edges
- [ ] **Entity Curation**: Manual entity management interface
- [ ] **Graph Comparison**: Compare graphs across time periods
- [ ] **Confidence Scores**: Show relationship confidence
- [ ] **Causal Reasoning**: Identify causal relationships

---

## Related Documentation

- [Document Ingestion Strategy](../document-ingestion-strategy.md) - How documents feed into tri-search
- [Memory Architecture](../concept/memory-architecture.md) - Overall memory system design
- [AI Periodic Table Roadmap](../../ai-periodic-table-roadmap.md) - Gk element details
- [Agent Personas](../../AGENTS.md) - How agents use graph knowledge
- [Gk Technical Specification](gk-graph-knowledge-technical.md) - Node/edge taxonomy, enrichment, invariants

---

## Support

For questions or issues:

1. Check the [Knowledge Graph interface](https://engram.work/memory/graph)
2. Review [API documentation](../../reference/api/)
3. Open an issue in the repository
4. Contact the Engram team

---

*Last Updated: January 2026*  
*Version: 1.0*

