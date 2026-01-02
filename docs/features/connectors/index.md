---
layout: default
title: Connectors
parent: Features
---

# Connectors

Data ingestion connectors for the Engram Context Engineering Platform.

## Document Ingestion

The primary connector for enterprise knowledge is the **Document Ingestion Pipeline**:

- [📄 Document Ingestion Strategy](../../document-ingestion-strategy.md) - Full documentation with tri-search architecture

## Connector Types

| Connector | Status | Description |
|-----------|--------|-------------|
| File Upload | ✅ Implemented | PDF, DOCX, TXT, MD via `/api/v1/etl/ingest` |
| SharePoint | 🔶 Planned | Enterprise document libraries |
| Confluence | 🔶 Planned | Wiki pages and spaces |
| GitHub | 🔶 Planned | Source code and documentation |
| ServiceNow | 🔶 Planned | Tickets and incidents |

## Architecture

Connectors feed into the tri-indexing pipeline:

1. **Keyword Layer** - Zep sessions for BM25 search
2. **Vector Layer** - pgvector embeddings for semantic search
3. **Graph Layer** - Zep facts for knowledge graph queries

## Related

- [Document Ingestion Strategy](../../document-ingestion-strategy.md)
- [Connectors Plan](connectors-plan.md)
