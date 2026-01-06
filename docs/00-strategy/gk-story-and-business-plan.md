---
layout: default
title: Gk (Graph Knowledge) — Story & Business Plan Copy
nav_exclude: true
---

# Gk (Graph Knowledge) — the Differentiator

## Why this matters (directional guidance)

As agents become action-oriented and cross-system, the fragility is less about the model and more about whether the agent pulled **the right value from the right system at the right time**.

Enterprises already have systems of record (Salesforce, Netsuite, Zendesk, data warehouses), but what’s often missing is the layer that actually runs the business day-to-day:
- decision traces
- exceptions and overrides
- approvals that happen outside structured systems
- “policy in practice” learned through repeated edge cases

This is the **what vs why gap**.

**Gk is Engram’s implementation of this idea.** It captures the connections between entities and events over time, with provenance, so autonomy can be audited and improved. The output isn’t just an answer — it’s a **queryable record of how decisions were made**.

## Positioning (marketing-ready)

Engram’s defining advantage is **Gk (Graph Knowledge)**: the layer that turns memory from “similar text retrieval” into **connected, auditable understanding** — what happened and why.

Most systems stop at two modes of recall:
- **Keyword**: exact matches (fast, brittle)
- **Vector**: semantic similarity (powerful, but opaque)

Engram adds the third layer:
- **Gk**: relationships between entities, facts, episodes, topics, and metadata — with **provenance**.

This unlocks **emergent contextual awareness**: the system can follow chains of meaning across time (multi-hop), show how ideas connect, and explain *why* a result was returned.

In other words: systems of record tell you **state**; Gk adds **decision lineage**.

## Elena — business plan insert (copy/paste)

### Problem
Enterprises don’t just need answers — they need **continuity, traceability, and trust**. Vector-only retrieval struggles with multi-hop questions and cannot reliably explain the “why” behind decisions that live in Slack threads, calls, and tribal knowledge.

### Solution
Engram provides **provenance-first memory** powered by tri-search:
1. **Keyword search** for exact matches and terminology
2. **Vector search** for meaning and paraphrase
3. **Gk (Graph Knowledge)** for relationship traversal and auditability

Results are merged via **Reciprocal Rank Fusion (RRF)** to balance precision and recall.

### Differentiator / moat
**Gk is the moat** because it compounds:
- Every conversation/document becomes structured knowledge (entities + relationships)
- The graph enables multi-hop retrieval (A → B → C)
- The system can expose *provenance* (source, timestamp, agent/session)
- Transparency is productized via **Function Calls (Fc)**: users can see the API calls that produced the view, request timing, and the environment backing memory

### Why now
Enterprise adoption is bottlenecked by trust. Gk creates “trust surfaces”: explainability, traceability, and operational observability.

### Outcome
Engram becomes a system that not only answers, but **remembers responsibly** — capturing the decision traces that become searchable precedent.

## Sage — short story (brand narrative)

In most AI tools, memory is a mirror: it reflects what looks similar.

Engram’s memory is a **map**.

A map doesn’t just show places — it shows the roads between them. It shows what connects to what, how far it is, and how to get from one idea to the next.

That is what **Gk** is in Engram.

When a team asks, “Why are we doing this?” Gk doesn’t just retrieve a paragraph that sounds right. It can point to the meeting where the decision was made, the document where the constraint was introduced, the people involved, the topics that shaped it — and it can show the connections.

This is what turns a helpful assistant into something rarer: a system with **contextual continuity**. Not just answers, but understanding — with receipts.

And as those receipts accumulate, something compounds: exceptions become precedent, and precedent becomes a navigable map.

## Architecture (diagram)

```mermaid
flowchart LR
  subgraph UI[Frontend]
    KG[/Memory → Gk (Graph Knowledge)/]
    SR[/Memory → Search with Provenance/]
  end

  subgraph API[Backend API]
    MG[GET /api/v1/memory/graph]
    MS[POST /api/v1/memory/search]
    ME[GET /api/v1/memory/environments]
  end

  subgraph TRI[Tri-Search + Fusion]
    KW[Keyword]\n(BM25 / session metadata)
    VX[Vector]\n(pgvector embeddings)
    GK[Gk]\n(graph traversal)
    RRF[RRF Fusion]
  end

  subgraph STO[Stores]
    ZS[Zep Sessions]\n(episodic + keyword)
    ZG[Zep Graph]\n(facts + entities)
    PG[(Postgres + pgvector)]
  end

  KG --> MG
  SR --> MS
  KG --> ME

  MG --> GK
  MS --> RRF

  RRF --> KW
  RRF --> VX

## Example (decision trace)

When an agent proposes an exception (e.g., a renewal discount beyond policy), the CRM will store the final value, but Gk stores:
- which incidents/tickets were consulted
- which policy gates were evaluated
- which prior precedent was referenced
- who approved and why

Gk is how that “why” becomes first-class data.
  RRF --> GK

  KW --> ZS
  GK --> ZG
  VX --> PG

  ZS --> RRF
  ZG --> RRF
```
