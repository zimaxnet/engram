# Research: Featureform Concepts for Engram

**Objective**: Analyze [Featureform](https://github.com/featureform/featureform) and extract architectural patterns relevant to the Engram Context Engine.

## Executive Summary

Featureform's core innovation is the **"Virtual Feature Store"**—it doesn't store data itself but *orchestrates* transformations and serving across existing infrastructure (Snowflake, Spark, Redis). It treats features as immutable, versioned code artifacts with strict lineage.

**Relevance to Engram**: Highly relevant. Engram aims to be a "Context Engine" that orchestrates memory (Zep), application state (Postgres), and identity (Entra ID). Adopting a **"Virtual Context Store"** pattern would allow Engram to unify these disparate sources into a single, versioned, and governable "Context API" for agents.

---

## Generated Architecture Diagram

The following architecture visually represents the **"Virtual Context Store"**, isolating the Virtual Orchestration layer from the Physical Infrastructure.

![Engram Virtual Context Store Architecture](/Users/derek/.gemini/antigravity/brain/e9bb0bec-2895-432e-8530-a87e9f46883a/uploaded_image_1766095965610.png)

---

## Key Concepts & Engram Translation

| Featureform Concept | Definition | Engram Equivalent (Proposed) | Benefit for Engram |
| :--- | :--- | :--- | :--- |
| **Virtual Feature Store** | An abstraction layer that orchestrates data infra without owning storage. | **Virtual Context Engine** | Unifies Zep (Semantic), Postgres (Episodic), and Graph (Knowledge) under one API without migrating data. |
| **Providers** | The physical infrastructure (Snowflake, Redis, Spark). | **Context Providers** | Zep, PostgreSQL, Azure AI, Microsoft Graph. |
| **Transformations** | Declarative logic (PySpark/SQL) to turn raw data into features. | **Context Pipelines** | Declarative ETL logic (Unstructured.io) that turns raw documents/chats into "Facts" or "Memories". |
| **Lineage (DAG)** | Immutable tracking of how a feature was derived from raw data. | **Memory Provenance** | Tracking which document, chat, or user action generated a specific fact in the Knowledge Graph. |
| **Training vs. Serving** | Point-in-time correct data for training vs. low-latency data for inference. | **Analysis vs. Injection** | **Analysis**: Batch processing of history for insights. **Injection**: Real-time context retrieval for Agent prompts. |
| **Immutable Resources** | Features/Transformations cannot be changed, only versioned. | **Immutable Context** | "Facts" in the graph are versioned. If logic changes (e.g., better chunking), new versions of facts are created. |

## Detailed Architectural Proposals

### 1. The "Virtual Context Store" Pattern

Instead of Engram just being a wrapper around Zep, it should be an *orchestrator*.

- **Current**: Application -> Engram -> Zep
- **Proposed**: Application -> Engram (Virtual Store) -> [Zep (Hot Memory), Postgres (State), Blob Storage (Archives)]
- **Benefit**: Agents request `user_context_v1` and Engram decides whether to fetch from Zep (fast) or compute it from Postgres logs (complete).

### 2. Context-as-Code (Definitions)

Featureform defines features in Python:

```python
@local.df
def average_user_transaction(transactions):
    return transactions.groupby("user_id")["amount"].mean()
```

Engram can define "Context Sets" similarly:

```python
@engram.context
def security_posture(vulnerabilities, user_role):
    # Combines data from different providers
    return {
        "critical_vulns": vulnerabilities.filter(severity="critical"),
        "access_level": user_role
    }
```

This moves prompt engineering logic ("what context do I need?") out of the Agent and into a managed **Context Definition Layer**.

### 3. Training/Serving Split -> RAG Pipeline Split

Featureform distinguishes between "Training Sets" (offline) and "Inference" (online).
For Engram:

- **Offline (Analysis)**: "Golden Thread" validation, deep learning optimization of the graph, re-indexing wikis.
- **Online (Inference)**: The `/api/v1/memory/enrich` endpoint that serves ultra-fast context to the Voice agent.
- **Action**: Explicitly separate these pipelines in the codebase to optimize for latency (Online) vs. throughput (Offline).

### 4. Lineage for Trust

In Featureform, you know exactly which SQL query produced a feature.
In Engram, we need **Context Provenance**:

- *"Why does the agent think I live in New York?"*
- **Answer**: Trace Context ID `C-123` -> Drived from Fact `F-456` -> Extracted by `Ingest-v2` -> From Message `M-789` ("I'm moving to NY next week").

## Recommendation for Campaign

**Pivot the "Context Engine" to be a "Virtual Context Store".**

1. **Define Context Providers**: Formalize the interfaces for Zep, Postgres, and external APIs.
2. **Implement Declarative definitions**: Allow defining "Context Views" in Python code rather than hardcoding SQL/Vector searches in routers.
3. **Visual Lineage**: Use the metadata in Zep to build a DAG of how knowledge is derived.

## MCP Integration Strategy

The Virtual Context Store is **ideal** for the Model Context Protocol (MCP). It allows us to expose the "Virtual" layer directly to any LLM client (Claude, Cursor, or Engram Agents).

| Virtual Store Concept | MCP Concept | Implementation Example |
| :--- | :--- | :--- |
| **Context Views** | **Resources** | `context://projects/delta/status` (Returns latest computed md/json) |
| **Context Functions** | **Tools** | `get_user_context(user_id="u-123")` |
| **Lineage/DAG** | **Prompts** | `explain_context(fact_id="f-789")` |

**Why this wins**:

- **Zero-Copy**: The LLM client doesn't need to index your SharePoint. It just mounts the `context://` resource.
- **Security**: The Virtual Store handles the ACLs; MCP just pipes the result.
- **Portability**: The same "Context Store" works for a Voice Agent (via tool call) and a Human User (via Claude Desktop resource viewer).
