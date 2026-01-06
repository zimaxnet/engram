---
layout: default
title: Gk (Graph Knowledge) — Technical Specification
parent: Memory
nav_order: 2
---

# Gk (Graph Knowledge) — Technical Specification

This document is a technical, implementation-accurate description of Engram’s **Gk (Graph Knowledge)** layer and its integration into tri-search. It is written to be used as a design + verification reference for engineering, observability, and product correctness.

## 1. Scope and definitions

### 1.1 Tri-search retrieval stack

Engram retrieval is the union of three retrieval modalities:

1. **Keyword (lexical) retrieval** over episodic content and metadata.
2. **Vector (semantic) retrieval** over embeddings (e.g., pgvector).
3. **Gk (graph) retrieval** over a typed, attributed graph of nodes and edges (facts, episodes, topics, provenance).

These are fused downstream using **Reciprocal Rank Fusion (RRF)**:

$$
\operatorname{RRF}(d) = \sum_{i \in \{K,V,G\}} \frac{1}{k + r_i(d)}
$$

Where $r_i(d)$ is the rank of candidate $d$ returned by retriever $i$, and $k$ is a constant (commonly 60) stabilizing early-rank dominance.

### 1.2 Gk as an attributed multigraph

Gk is modeled as an **attributed, typed graph** $\mathcal{G} = (\mathcal{V}, \mathcal{E})$:

- Nodes $v \in \mathcal{V}$ have:
  - `id`: stable identifier
  - `node_type`: type label (Fact/Entity/Memory/Topic/Meta)
  - `content`: human-readable label
  - `metadata`: key-value attributes used for provenance and routing
  - `degree`: computed connectivity metric used for diagnostics and UI affordances

- Edges $e \in \mathcal{E}$ have:
  - `source`, `target`
  - `label`: semantic edge type
  - `weight`: relationship weight (currently uniform 1.0)

In the current implementation, Gk is returned as a node/edge list plus summary statistics.

## 2. Data sources and construction pipeline

Gk is built from two primary sources:

1. **Semantic facts** (when available) retrieved via the memory provider’s facts interface.
2. **Episodic sessions** (episodes) retrieved via the sessions interface, including session metadata such as `summary`, `topics`, `agent_id`, `turn_count`, and optional provenance fields.

### 2.1 Graph construction (reference implementation)

Reference implementation lives in:
- [backend/api/routers/memory.py](backend/api/routers/memory.py)

The construction procedure can be summarized as:

1. Ingest Fact nodes from `get_facts(user_id, query, limit)`.
2. Ingest Episode nodes from `list_sessions(user_id, limit)`.
3. Create Topic nodes from episode metadata and connect Episode→Topic edges.
4. Derive provenance Meta nodes from Fact metadata and connect Fact→Meta edges.
5. **Enrichment pass** (relationship type expansion):
   - Fact→Topic edges when fact metadata contains `topic` or `topics`.
   - Fact→Agent edges when fact metadata contains `agent_id`.
   - Episode→Agent edges when episode metadata contains `agent_id`.
   - Episode→Meta edges for provenance keys when present.
6. Compute degrees and statistics.

## 3. Node taxonomy (typed semantics)

Gk uses the following node types.

### 3.1 `fact`
A fact is a semantic unit of knowledge. It can be derived from:
- conversation statements
- document ingestion
- manual additions

Facts carry metadata intended for provenance and downstream trust surfaces.

### 3.2 `memory`
An episode/session node representing a bounded conversation context.

The implementation stores a short label for graph legibility, while preserving full summary content in metadata.

### 3.3 `topic`
A topic node represents a normalized conversation theme. Topics are primarily sourced from episode metadata.

### 3.4 `entity`
Entity nodes capture named participants or conceptual anchors. The current enrichment generates **agent entities** from `agent_id` as a first-class entity subtype.

### 3.5 `meta`
Meta nodes represent provenance attributes (e.g., source, filename, tenant, channel). Meta nodes are explicitly typed as `meta` so the UI can render them distinctly.

## 4. Relationship types (edge semantics)

Edge labels are not cosmetic; they determine which traversals are meaningful for multi-hop reasoning.

### 4.1 Episode-to-Topic: `concerns`
Represents topical coverage of a conversation episode.

- `memory` → `topic`
- label: `concerns`

### 4.2 Fact-to-Meta: `{source|filename|etl_source|tenant_id|topic|kind|role}`
Provenance link from a fact to a metadata atom.

- `fact` → `meta`
- label: metadata key

### 4.3 Episode-to-Agent: `by`
Attribution edge from an episode to the agent that produced it.

- `memory` → `entity(kind=agent)`
- label: `by`

### 4.4 Fact-to-Agent: `attributed_to`
Attribution edge from a fact to an agent.

- `fact` → `entity(kind=agent)`
- label: `attributed_to`

### 4.5 Fact-to-Topic: `about`
Semantic association between a fact and a topic.

- `fact` → `topic`
- label: `about`

### 4.6 Episode-to-Meta (provenance)
Provenance edges from episode nodes to meta nodes, for keys:
- `tenant_id`, `channel`, `source`, `filename`

- `memory` → `meta`
- label: key

## 5. Provenance surfaces and “Fc” transparency

Gk is only valuable in enterprise settings if it can be inspected. Engram productizes this inspection via two transparency surfaces:

### 5.1 Function Calls (Fc)
The UI explicitly maps views to API endpoints (including request timing) so users can validate what produced the visualization.

Reference UI:
- [frontend/src/pages/Memory/KnowledgeGraph.tsx](frontend/src/pages/Memory/KnowledgeGraph.tsx)

### 5.2 Environment visibility
The UI displays environment metadata used by memory tooling.

Reference endpoints:
- `GET /api/v1/memory/graph`
- `GET /api/v1/memory/environments`

Reference implementation:
- [backend/memory/environments.py](backend/memory/environments.py)

## 6. Diagnostics and interpretation

### 6.1 Degree
Degree is computed as the count of incident edges. It is used as:
- a lightweight centrality proxy
- a filter (min degree) to reduce noise on mobile
- a signal for “hubness” (nodes that connect multiple concepts)

### 6.2 Graph density expectations
A healthy Gk graph is not “max nodes” but “useful edges.” Enrichment adds edges that reflect:
- attribution (who)
- topical alignment (what it’s about)
- provenance (where it came from)

## 7. Correctness constraints (scientific-style invariants)

The following invariants should hold:

1. **Type fidelity**: meta nodes must be typed `meta` (not `entity`) to preserve semantic rendering and filtering.
2. **Attribution edges**: if `agent_id` exists on an episode or fact, the corresponding edge must exist.
3. **Provenance completeness**: if provenance keys exist, they must be representable as Meta nodes and linked.
4. **User isolation**: graph construction must be scoped by authenticated `user_id` boundaries.

## 8. Roadmap (research-grade extensions)

If/when needed, Gk can evolve into a higher-order system with:
- weighted edges learned from usage
- temporal validity windows and time slicing
- community detection and concept clustering
- explicit path explanations (multi-hop provenance trails)
- retriever contribution attribution per result (keyword vs vector vs graph)

---

Last updated: January 2026
