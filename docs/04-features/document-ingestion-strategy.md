---
layout: default
title: "Document Ingestion Strategy"
parent: "Feature Specs"
---

# Document Ingestion Strategy: Enterprise Guide

> **Engram Context Engineering Platform**  
> Aligns with GTM Research Paper v2 Pilot Requirements

![Document Ingestion Strategy](/assets/diagrams/engram-document-ingestion-strategy.png)

---

## Executive Summary

The Engram Document Ingestion Strategy enables enterprises to ingest documents from **5 source types** into a unified context engine, making content searchable via **tri-search** (keyword, vector, graph). This architecture directly addresses the GTM pilot requirements from the Context Engineering Research Paper.

---

## GTM Alignment: 5 Pilot Source Types

| Source Type | GTM Requirement | Engram Implementation | Status |
|-------------|-----------------|----------------------|--------|
| **Policies** | Governance docs, procedures | Unstructured PDF/DOCX → Tri-index | ✅ Implemented |
| **Tickets** | Issue trackers, case records | API connectors → Session episodes | 🔶 Planned |
| **PDFs** | Dense documents, reports | Unstructured partition → Chunking | ✅ Implemented |
| **Wikis** | Knowledge bases, Confluence | Wiki connector → `doc-wiki-*` sessions | ✅ Implemented |
| **Code** | Source files, configs | Git integration → Code-aware chunking | 🔶 Planned |

---

## Tri-Search Architecture

Every ingested document is indexed into **three search layers**, enabling comprehensive retrieval via Reciprocal Rank Fusion (RRF):

### 1. Keyword Search (BM25/Lexical)

- **Storage**: Zep sessions with messages
- **Session Pattern**: `doc-upload-{uuid}`
- **Enables**: Exact phrase matching, acronym lookup

### 2. Vector Search (Semantic)

- **Storage**: `memory_embeddings` table (pgvector)
- **Embedding Model**: `text-embedding-3-small` (1536 dims)
- **Enables**: Conceptual similarity, paraphrase matching

### 3. Graph Search (Knowledge Graph)

- **Storage**: Zep facts per user
- **Enables**: Entity relationships, temporal facts, multi-hop reasoning

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENT UPLOAD                          │
│                  (PDF, DOCX, TXT, etc.)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 UNSTRUCTURED PROCESSOR                       │
│  • partition()     - Layout-aware extraction                 │
│  • chunk_by_title  - Semantic chunking (1000 char max)       │
│  • Metadata        - Page numbers, filetype, provenance      │
└─────────────────────────┬───────────────────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
┌───────────────┐ ┌─────────────┐ ┌─────────────┐
│   KEYWORD     │ │   VECTOR    │ │   GRAPH     │
│   LAYER       │ │   LAYER     │ │   LAYER     │
├───────────────┤ ├─────────────┤ ├─────────────┤
│ add_memory()  │ │ store_with_ │ │ add_fact()  │
│ to session    │ │ embedding() │ │ to user     │
│               │ │             │ │             │
│ Zep Sessions  │ │ pgvector    │ │ Zep Facts   │
│ `doc-upload-* │ │ memory_     │ │ Knowledge   │
│               │ │ embeddings  │ │ Graph       │
└───────────────┘ └─────────────┘ └─────────────┘
            │             │             │
            └─────────────┼─────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID SEARCH                             │
│            Reciprocal Rank Fusion (RRF)                      │
│  search_memory() combines all three result sets              │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Implementation

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| `DocumentProcessor` | `backend/etl/processor.py` | Unstructured partition + chunking |
| `IngestionService` | `backend/etl/ingestion_service.py` | Tri-indexing orchestration |
| `ZepMemoryClient` | `backend/memory/client.py` | Keyword + graph storage |
| `VectorStore` | `backend/memory/vector_store.py` | Embedding storage + search |
| `EmbeddingClient` | `backend/memory/embedding_client.py` | Azure OpenAI embeddings |

### API Endpoint

```
POST /api/v1/etl/ingest
Content-Type: multipart/form-data

Parameters:
  file: <document binary>
  
Response:
{
  "success": true,
  "filename": "policy-v2.pdf",
  "chunks_processed": 42,
  "session_id": "doc-upload-a1b2c3d4",
  "document_id": "doc-e5f6g7h8i9j0"
}
```

### Ingestion Flow (Background Task)

```python
async def index_chunks_tri(chunks, user_id, filename, doc_id, session_id):
    # 1. Create session for keyword search
    await memory_client.get_or_create_session(
        session_id=session_id,
        user_id=user_id,
        metadata={"title": filename, "document_id": doc_id}
    )
    
    for chunk in chunks:
        # Layer 1: Graph (facts)
        await memory_client.add_fact(user_id, fact=chunk.text, metadata={...})
        
        # Layer 2: Vector (embeddings)
        await store_with_embedding(session_id, content=chunk.text, source_type="document")
        
        # Layer 3: Keyword (session messages)
        await memory_client.add_memory(session_id, messages=[...])
```

---

## Context Layer Integration

Document ingestion populates **Layer 3: Semantic Knowledge** of the 4-Layer Enterprise Context Schema:

| Layer | Populated By | Document Role |
|-------|--------------|---------------|
| Layer 1: Security | Azure Entra ID | User permissions filter document access |
| Layer 2: Episodic | Chat/Voice | Conversation about documents |
| Layer 3: Semantic | **Document Ingestion** | Facts and entities from documents |
| Layer 4: Operational | Temporal | Durable ingestion workflows |

---

## Pilot Success Criteria (GTM Alignment)

From the GTM Research Paper, document ingestion supports:

### Retrieval Metrics

- ✅ **Hit@1/Hit@3**: Tri-search improves first-result accuracy
- ✅ **No-answer reduction**: Graph relationships surface related content

### Faithfulness Metrics

- ✅ **Grounded responses**: Facts include provenance metadata
- ✅ **Citation correctness**: `document_id` + `chunk_index` enable citations

### Governance Metrics

- ✅ **Audit logs**: Ingestion logged with user_id, filename, timestamp
- ✅ **Tenant isolation**: User-scoped facts prevent cross-tenant leakage

---

## Connector Roadmap

### Phase 1: File Upload (Implemented)

- Manual upload via API/UI
- Supported: PDF, DOCX, TXT, MD
- Processing: Unstructured.io

### Phase 2: Enterprise Connectors (Planned)

| Connector | Source Type | Priority |
|-----------|-------------|----------|
| SharePoint | Policies, wikis | High |
| Confluence | Wikis | High |
| GitHub | Code | Medium |
| ServiceNow | Tickets | Medium |
| S3/Azure Blob | All | High |

### Phase 3: Real-time Sync

- Webhook-based incremental updates
- Bi-temporal tracking (valid time + transaction time)
- Contradiction detection for updated facts

---

## References

- [GTM Research Paper](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/docs/Engram_Context_Engineering_GTM_Research_Paper_v2.html)
- [4-Layer Context Schema](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/docs/4-layer-context-schema-story.md)
- [Visual Art Ingestion Spec](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/docs/mobile-feature-specs/001-visual-art-ingestion.md)
- [Structured Document Scanning](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/docs/mobile-feature-specs/002-structured-document-scanning.md)
