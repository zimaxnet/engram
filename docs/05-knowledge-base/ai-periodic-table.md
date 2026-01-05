---
layout: default
title: "AI Periodic Table — Engram Capability Matrix"
parent: "Knowledge Base"
---

# AI Periodic Table — Engram Capability Matrix

> **Engram's competitive position mapped to Martin Keen's AI Periodic Table framework.**

## Video Introduction

<iframe width="560" height="315" src="https://www.youtube.com/embed/ESBMgZHzfG0?si=Q2GME-RqGHjGaz_6" title="Martin Keen - AI Periodic Table Explained" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

*Credit: [Martin Keen](https://www.linkedin.com/in/martingkeen/), IBM Master Inventor | [Video](https://www.youtube.com/watch?v=ESBMgZHzfG0)*

---

## Interactive Matrix

📊 **[View Full Interactive Matrix](../ai-periodic-table-matrix.html)**

---

## Status Legend

| Status | Meaning | Count |
|--------|---------|-------|
| 🟢 Strong | Production-ready implementation | 12 |
| 🟡 Emerging | Partial implementation or roadmap | 1 |
| 🔴 Gap | Not yet implemented | 3 |
| ⭐ Unique | Competitive differentiator | 1 |

---

## Element-by-Element Breakdown

### Row 1: Primitives

| Element | Symbol | Status | Engram Component | Dashboard |
|---------|--------|--------|------------------|-----------|
| Prompts | Pr | 🟢 Strong | Agent system prompts | [Agent Config](../agents.md) |
| Embeddings | Em | 🟢 Strong | Zep embedding layer | [Zep Cloud](https://cloud.getzep.com) |
| LLM | Lg | 🟢 Strong | Claude, Gemini, GPT-4o | [Azure AI](https://portal.azure.com) |

### Row 2: Compositions

| Element | Symbol | Status | Engram Component | Dashboard |
|---------|--------|--------|------------------|-----------|
| Function Call | Fc | 🟢 Strong | **Story Gen** `delegate_to_sage`<br>**GH Issues** `create_github_issue`<br>**OneDrive** `save_to_onedrive` | [MCP Docs](../mcp.md) |
| Vector | Vx | 🟢 Strong | Zep Tri-Search (Vector Layer) | [Zep Cloud](https://cloud.getzep.com) |
| RAG | Rg | 🟢 Strong | Context assembly pipeline (Tri-Search Fusion) | [Architecture](../architecture.md) |
| Guardrails | Gr | 🟢 Strong | Azure Entra ID | [Entra Admin](https://entra.microsoft.com) |
| Multimodal | Mm | 🟢 Strong | Imagen 3.0 + VoiceLive | [Azure AI](https://portal.azure.com) |

### Row 3: Deployment

| Element | Symbol | Status | Engram Component | Dashboard |
|---------|--------|--------|------------------|-----------|
| Agent | Ag | 🟢 Strong | Elena, Marcus, Sage | [Agent Config](../agents.md) |
| Finetune | Ft | 🔴 Gap | *Roadmap: Granite/Llama* | — |
| Framework | Fw | 🟢 Strong | Temporal workflows | [Temporal UI](https://temporal.engram.work) |
| Red-team | Rt | 🟡 Emerging | Basic validation | — |
| Small | Sm | 🔴 Gap | *Roadmap: Phi-4/Granite* | — |

### Row 4: Emerging

| Element | Symbol | Status | Engram Component | Dashboard |
|---------|--------|--------|------------------|-----------|
| Multi-agent | Ma | 🟢 Strong | Agent delegation | [Workflow Monitor](https://temporal.engram.work) |
| Synthetic | Sy | 🟢 Strong | Story + visual gen | [Stories](https://engram.work/stories) |
| **Graph Knowledge** | **Gk** | ⭐ **Unique** | **Zep Temporal KG + Visualization** | [Graph Interface](https://engram.work/memory/graph) |
| Interpret | In | 🔴 Gap | *Roadmap: Explainability* | — |
| Thinking | Th | 🟢 Strong | Extended reasoning | [Workflow Monitor](https://temporal.engram.work) |

---

## Gk (Graph Knowledge) — Our Unique Advantage

> **Symbol**: Gk  
> **Position**: Row 4 (Emerging) × Column 3 (Orchestration)  
> **Definition**: Temporal knowledge graphs for dynamic context orchestration  
> **Status**: ⭐ **Unique Differentiator** — Production-ready with enhanced visualization

### Why Gk Matters

While competitors use static RAG (retrieve → augment → generate), Engram uses **dynamic Graph Knowledge orchestration**:

| Aspect | Static Frameworks (Fw) | Graph Knowledge (Gk) |
|--------|------------------------|----------------------|
| Routing Logic | Predefined chains/DAGs | Dynamic, semantic routing |
| Context Assembly | Manual prompt engineering | Automatic via graph traversal |
| Memory | Stateless or session-scoped | Temporal, multi-session knowledge |
| Discovery | Explicit tool registration | Emergent via entity relationships |

### Tri-Search: The Complete Picture

Graph Knowledge is the **critical third layer** of Engram's tri-search capability:

1. **Keyword Search (BM25)**: Exact phrase matching, acronym lookup
2. **Vector Search (Semantic)**: Conceptual similarity via embeddings
3. **Graph Search (Gk)**: Relationship traversal, multi-hop reasoning ⭐

Results from all three layers are combined using **Reciprocal Rank Fusion (RRF)** for optimal retrieval.

**📖 Full Documentation**: [Graph Knowledge & Tri-Search Guide](../features/memory/graph-knowledge-tri-search.md)

### Implementation

Engram implements Gk through [Zep Cloud](https://cloud.getzep.com/):

- **Entity Extraction**: Automatic extraction from conversations and documents
- **Fact Linking**: Relationships stored as graph edges with timestamps
- **Temporal Awareness**: Facts have timestamps, enabling time-aware queries
- **Cross-Session Learning**: Knowledge compounds automatically across conversations
- **Visualization**: Interactive graph interface at `/memory/graph`

### Graph Knowledge Interface

**Access**: [Knowledge Graph Visualization](https://engram.work/memory/graph)

**Features**:
- **Interactive Force-Directed Graph**: Visualize relationships between entities, facts, episodes, and topics
- **Search & Filter**: Query-based filtering, node type filters, degree-based filtering
- **Statistics Dashboard**: Total nodes/edges, average degree, node type breakdown
- **Node Details**: Full content, metadata, connections, and traversal paths
- **Tri-Search Context**: Explanation of how Graph Knowledge fits into tri-search

**Node Types**:
- **Facts** (Cyan): Semantic facts extracted from conversations
- **Entities** (Purple): People, projects, concepts
- **Episodes** (Green): Conversation sessions/episodic memory
- **Topics** (Amber): Conversation themes and topics
- **Metadata** (Gray): Source tags, filenames, tenant IDs

### Use Cases

1. **Entity Discovery**: "Who worked on the authentication project?" → Traverse graph to find connected people
2. **Project Timeline**: "What happened with Project Alpha over time?" → Chronological episode traversal
3. **Knowledge Gap Analysis**: Identify isolated nodes (low degree) that need more context
4. **Multi-Hop Reasoning**: "What did Elena say about topics related to security?" → Multi-step graph traversal

### Observability

**What You Can See**:
- ✅ Graph structure and relationships
- ✅ Node details (content, metadata, connections)
- ✅ Statistics (total nodes, edges, degree metrics)
- ✅ Search transparency (which nodes match query)

**Roadmap**:
- 🔄 Tri-search breakdown (which layer contributed each result)
- 🔄 Retrieval path visualization
- 🔄 Graph analytics (centrality, community detection)
- 🔄 Time slider (view graph at different time points)

---

## Dashboards & Observability

| System | Dashboard | Purpose |
|--------|-----------|---------|
| Azure AI | [Portal](https://portal.azure.com) | Model deployments, costs |
| Temporal | [UI](https://temporal.engram.work) | Workflow monitoring |
| Zep | [Cloud](https://cloud.getzep.com) | Memory, embeddings, graph |
| Knowledge Graph | [Interface](https://engram.work/memory/graph) | Graph visualization, tri-search layer 3 |
| Entra ID | [Admin](https://entra.microsoft.com) | Authentication, RBAC |
| Cost Management | [Azure](https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/costanalysis) | FinOps |

---

## Provenance

- **Baseline Date**: January 5, 2026
- **Framework Source**: [Martin Keen's AI Periodic Table](https://youtu.be/ESBMgZHzfG0?si=Q2GME-RqGHjGaz_6)
- **Milestone Document**: [2026-01-05-ai-periodic-table-baseline.md](../milestones/2026-01-05-ai-periodic-table-baseline.md)

---

## Related Documents

- [Business Plan](../business-plan-ai-periodic-table.md)
- [Interactive Matrix](../ai-periodic-table-matrix.html)
- [Architecture Overview](../architecture.md)
- [Graph Knowledge & Tri-Search Guide](../features/memory/graph-knowledge-tri-search.md) - Comprehensive documentation
- [AI Periodic Table Roadmap](../ai-periodic-table-roadmap.md) - Detailed element mapping
