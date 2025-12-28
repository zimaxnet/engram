#!/usr/bin/env python3
"""
Ingest Semantic Search Capability Episode.

Documents the custom pgvector-based semantic search implementation
that bypasses Zep OSS limitations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
SESSION_ID = "capability-semantic-search"
USER_ID = "system"

EPISODE_CONTENT = """
# Capability: Custom Semantic Search with pgvector (Dec 28, 2025)

## Summary
Built a complete semantic search system that bypasses Zep OSS limitations by using pgvector directly in Postgres. This demonstrates development prowess and adds significant value to the Engram platform.

## Architecture

```
User Query
    ├── Semantic Search (pgvector cosine similarity)
    │       ↓
    │   text-embedding-3-small → vector(1536) → ivfflat index
    │
    └── Keyword Search (Zep sessions)
            ↓
    Reciprocal Rank Fusion (RRF, k=60)
            ↓
    Combined Results (sorted by RRF score)
```

## Components Built

### 1. Database Migration
- **File**: `migrations/001_create_memory_embeddings.sql`
- **Table**: `memory_embeddings` with `vector(1536)` column
- **Index**: ivfflat for cosine similarity search
- **Database**: `zep` on Azure Postgres Flexible Server

### 2. Embedding Client
- **File**: `backend/memory/embedding_client.py`
- **Model**: `text-embedding-3-small` (zimax-gw gateway)
- **Dimensions**: 1536
- **Provider**: Azure OpenAI via APIM gateway

### 3. Vector Store
- **File**: `backend/memory/vector_store.py`
- **Client**: asyncpg for direct Postgres access
- **Operations**: store_embedding(), search_similar()
- **Convenience**: store_with_embedding(), semantic_search()

### 4. Hybrid Search
- **File**: `backend/memory/client.py` (search_memory method)
- **Fusion**: Reciprocal Rank Fusion with k=60
- **Phases**:
  1. Semantic search via pgvector (cosine similarity)
  2. Keyword search via Zep sessions
  3. RRF fusion combining both sources

### 5. Ingestion Scripts
- **Migration Runner**: `scripts/run_migration.py`
- **Embedding Ingestor**: `scripts/ingest_embeddings.py`
- **Results**: 93 sessions ingested successfully (0 failed)

## Ingested Content Types
| Type | Count | Examples |
|------|-------|----------|
| Episodes | 18 | sess-vision-001, sess-agentic-framework-001 |
| Documents | 48 | doc-enterprise-auth-strategy |
| Wiki Pages | 19 | doc-wiki-architecture, doc-wiki-finops |
| Conversations | 6 | chat-demo-* |
| Findings | 2 | finding-startup-auth-zep-url-fix |

## Why Custom Over Zep Cloud
- **Zep OSS Limitation**: No vector search endpoint (404 on /memory/search)
- **Zep Cloud Cost**: ~$99/month
- **Custom Solution**: Demonstrates development capability
- **Business Value**: Adds to Elena's business plan

## Validation
Elena successfully answered "What is the recursive self-awareness vision?" by citing Brain (Zep) and Spine (Temporal) architecture - knowledge retrieved from ingested episodes.

## Key Technical Decisions
1. **text-embedding-3-small**: ada-002 not deployed on zimax-gw
2. **ivfflat index**: Faster than hnsw for small datasets
3. **RRF fusion**: Industry-standard hybrid search algorithm
4. **asyncpg**: Native PostgreSQL driver for async operations
5. **Graceful fallback**: Semantic search failure doesn't block keyword search

## Files Modified
1. `backend/memory/client.py` - Added hybrid search with RRF
2. `backend/memory/embedding_client.py` - Azure OpenAI embeddings
3. `backend/memory/vector_store.py` - pgvector CRUD operations
4. `migrations/001_create_memory_embeddings.sql` - Database schema
5. `scripts/run_migration.py` - Python migration runner
6. `scripts/ingest_embeddings.py` - Batch embedding ingestion

## Next Steps
- Phase 3: Knowledge Graph (Graphiti) - On standby
- CIAM Integration: Azure AD B2C or Google login to solve recurring 401
"""

METADATA = {
    "type": "capability",
    "date": "2025-12-28",
    "topics": ["semantic search", "pgvector", "embeddings", "RAG", "hybrid search", "RRF"],
    "summary": "Custom semantic search implementation using pgvector with 93 sessions ingested",
    "components": ["embedding_client.py", "vector_store.py", "client.py"],
}


async def main():
    print("🚀 Ingesting Semantic Search Capability Episode")
    print(f"Target: {ZEP_URL}")
    print(f"Session: {SESSION_ID}")
    print("-" * 50)
    
    settings = get_settings()
    settings.zep_api_url = ZEP_URL
    os.environ["ZEP_API_URL"] = ZEP_URL
    
    memory_client = ZepMemoryClient()
    
    # Ensure system user
    try:
        await memory_client._request("POST", "/api/v1/users", json={
            "user_id": USER_ID,
            "metadata": {"role": "system"}
        })
    except:
        pass
    
    # Create session
    try:
        await memory_client.get_or_create_session(SESSION_ID, USER_ID, METADATA)
        print(f"✅ Session: {SESSION_ID}")
    except Exception as e:
        print(f"ℹ️  Session note: {e}")
    
    # Add content
    await memory_client.add_memory(
        session_id=SESSION_ID,
        messages=[{"role": "system", "content": EPISODE_CONTENT}],
        metadata=METADATA
    )
    print(f"✅ Episode ingested ({len(EPISODE_CONTENT)} chars)")
    
    # Also add to vector store for semantic search
    try:
        from backend.memory.vector_store import store_with_embedding
        await store_with_embedding(
            session_id=SESSION_ID,
            content=EPISODE_CONTENT,
            title="Custom Semantic Search Capability",
            topics=METADATA["topics"],
            source_type="capability",
        )
        print("✅ Embedding stored in vector_store")
    except Exception as e:
        print(f"⚠️  Vector store: {e}")
    
    print("-" * 50)
    print("✅ Memory enrichment complete!")


if __name__ == "__main__":
    asyncio.run(main())
