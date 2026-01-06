---
layout: default
title: Foundry IQ POC Implementation
parent: Architecture
nav_order: 19
---

# Foundry IQ POC Implementation

> **Status**: 🚧 In Progress  
> **Date**: January 2026  
> **Feature**: Enterprise Document Search via Foundry IQ

---

## Overview

**Foundry IQ** is powered by Azure AI Search and provides unified access to enterprise documents from multiple sources (SharePoint, Fabric OneLake, web content). This POC integrates Foundry IQ with Engram's existing tri-search to create a **hybrid search** that combines:

- **Engram Tri-Search**: Episodic memory, conversation history, knowledge graph
- **Foundry IQ**: Enterprise documents, SharePoint, external knowledge bases

---

## Architecture

### Current State

**Engram Tri-Search**:
- ✅ Keyword Search (Zep sessions)
- ✅ Vector Search (pgvector embeddings)
- ✅ Graph Search (Knowledge Graph)

**Use Cases**:
- Conversation history
- Episodic memory
- Knowledge graph relationships
- Wiki pages
- Uploaded documents

### Target State

**Hybrid Search**:
```
User Query
    ├── Engram Tri-Search
    │   ├── Keyword Search (Zep)
    │   ├── Vector Search (pgvector)
    │   └── Graph Search (Knowledge Graph)
    │
    └── Foundry IQ
        └── Enterprise Documents (Azure AI Search)
            ├── SharePoint
            ├── Fabric OneLake
            └── Web Content
    
    ↓
    
Reciprocal Rank Fusion (RRF)
    ↓
Combined Results
```

---

## Implementation Plan

### Phase 1: Foundry IQ Client ✅

**Goal**: Create client for Foundry IQ API

**Tasks**:
1. Research Foundry IQ API endpoints
2. Create `FoundryIQClient` class
3. Implement search method
4. Handle authentication (Managed Identity or API key)

**Files**:
- `backend/agents/foundry_iq_client.py` (new)

### Phase 2: Hybrid Search Integration 🚧

**Goal**: Integrate Foundry IQ with Engram's search

**Tasks**:
1. Update `search_memory` to call Foundry IQ
2. Combine results using RRF
3. Add feature flag (`USE_FOUNDRY_IQ`)
4. Graceful fallback if Foundry IQ unavailable

**Files**:
- `backend/memory/client.py` (update)
- `backend/core/config.py` (add feature flag)

### Phase 3: Knowledge Base Setup

**Goal**: Create and configure Foundry IQ knowledge base

**Tasks**:
1. Create knowledge base in Azure AI Foundry
2. Connect data sources (SharePoint, OneLake, etc.)
3. Configure indexing
4. Test document ingestion

**Tools**:
- Azure Portal
- Foundry REST API
- Azure AI Search

### Phase 4: Testing & Validation

**Goal**: Validate hybrid search quality

**Tasks**:
1. Test with enterprise documents
2. Compare Engram-only vs. hybrid results
3. Measure latency and accuracy
4. Document findings

---

## Foundry IQ API Research

### Endpoints

Based on Azure AI Foundry documentation:

1. **Search Knowledge Base**:
   ```
   POST /api/projects/{project}/knowledge-bases/{kb_id}/search
   ```

2. **List Knowledge Bases**:
   ```
   GET /api/projects/{project}/knowledge-bases
   ```

3. **Get Knowledge Base**:
   ```
   GET /api/projects/{project}/knowledge-bases/{kb_id}
   ```

### Authentication

- **Managed Identity**: Default for production
- **API Key**: Fallback for POC/staging
- **Token Audience**: `https://ai.azure.com/.default`

### Request Format

```json
{
  "query": "user query text",
  "top": 10,
  "filters": {
    "source": "sharepoint",
    "date_range": {...}
  }
}
```

### Response Format

```json
{
  "results": [
    {
      "content": "document text",
      "source": "sharepoint://...",
      "score": 0.95,
      "metadata": {...}
    }
  ],
  "total_count": 42
}
```

---

## Integration Strategy

### Hybrid Search Flow

```python
async def hybrid_search(
    query: str,
    limit: int = 10,
    user: SecurityContext = None
) -> list[SearchResult]:
    """
    Hybrid search combining Engram tri-search and Foundry IQ.
    """
    settings = get_settings()
    
    # Phase 1: Engram Tri-Search (always)
    engram_results = await memory_client.search_memory(
        session_id="global-search",
        query=query,
        limit=limit,
        user_id=user.user_id if user else None,
    )
    
    # Phase 2: Foundry IQ (if enabled)
    foundry_results = []
    if settings.use_foundry_iq:
        foundry_iq_client = get_foundry_iq_client()
        if foundry_iq_client:
            try:
                foundry_results = await foundry_iq_client.search(
                    query=query,
                    limit=limit,
                    project_id=user.project_id if user else None,
                )
            except Exception as e:
                logger.warning(f"Foundry IQ search failed: {e}")
    
    # Phase 3: Combine using RRF
    if foundry_results:
        combined = reciprocal_rank_fusion([
            engram_results,
            foundry_results,
        ], k=60)
    else:
        combined = engram_results
    
    return combined[:limit]
```

### Feature Flag

```python
# backend/core/config.py
use_foundry_iq: bool = Field(False, alias="USE_FOUNDRY_IQ")
foundry_iq_knowledge_base_id: Optional[str] = Field(None, alias="FOUNDRY_IQ_KB_ID")
```

---

## Use Cases

### 1. Enterprise Document Search

**Scenario**: User asks "What's our Q4 sales strategy?"

**Engram Tri-Search**:
- Finds conversation history about Q4
- Finds wiki pages mentioning sales
- Finds related entities in knowledge graph

**Foundry IQ**:
- Finds SharePoint documents about Q4 strategy
- Finds OneLake data about sales metrics
- Finds external research about sales strategies

**Combined**: Comprehensive answer with both internal knowledge and enterprise documents

### 2. Technical Documentation

**Scenario**: User asks "How do we handle authentication?"

**Engram Tri-Search**:
- Finds architecture discussions
- Finds code examples from conversations
- Finds related authentication entities

**Foundry IQ**:
- Finds official documentation in SharePoint
- Finds API specifications
- Finds compliance documents

**Combined**: Both informal knowledge and formal documentation

### 3. Project Information

**Scenario**: User asks "What's the status of Project X?"

**Engram Tri-Search**:
- Finds conversation history about Project X
- Finds related entities and relationships
- Finds timeline information

**Foundry IQ**:
- Finds project documents in SharePoint
- Finds project plans and reports
- Finds external project references

**Combined**: Complete project context

---

## Benefits

### For Users

- ✅ **Broader Coverage**: Access to both conversational knowledge and enterprise documents
- ✅ **Better Answers**: More comprehensive responses with multiple sources
- ✅ **Unified Interface**: Single search across all knowledge

### For Engram

- ✅ **Leverage Azure AI Search**: Managed infrastructure, automatic indexing
- ✅ **Hybrid Approach**: Best of both worlds (Engram + Foundry)
- ✅ **Gradual Migration**: Can enable/disable via feature flag
- ✅ **No Breaking Changes**: Engram tri-search continues to work independently

---

## Configuration

### Environment Variables

```bash
# Enable Foundry IQ
USE_FOUNDRY_IQ=true

# Knowledge Base ID (from Azure Portal)
FOUNDRY_IQ_KB_ID=kb-12345678-1234-1234-1234-123456789012

# Foundry endpoint (already configured)
AZURE_FOUNDRY_AGENT_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_FOUNDRY_AGENT_PROJECT=zimax
```

### Azure Key Vault Secrets

- `foundry-iq-kb-id`: Knowledge base ID
- `foundry-iq-enabled`: Feature flag (true/false)

---

## Testing Plan

### Test Cases

1. **Engram-Only Search**:
   - Disable Foundry IQ
   - Verify Engram tri-search works as before
   - No regression

2. **Foundry IQ-Only Search**:
   - Disable Engram search (for testing)
   - Verify Foundry IQ returns enterprise documents
   - Check result quality

3. **Hybrid Search**:
   - Enable both Engram and Foundry IQ
   - Verify results combine correctly
   - Check RRF ranking

4. **Error Handling**:
   - Test with Foundry IQ unavailable
   - Verify graceful fallback to Engram-only
   - No errors in logs

### Success Metrics

- ✅ Search latency < 500ms (combined)
- ✅ Result quality improved (user feedback)
- ✅ No regression in Engram-only search
- ✅ Foundry IQ fallback works correctly

---

## Next Steps

1. **Research Foundry IQ API**:
   - Verify API endpoints
   - Test authentication
   - Understand response format

2. **Create Foundry IQ Client**:
   - Implement `FoundryIQClient` class
   - Add search method
   - Handle errors gracefully

3. **Integrate with Engram Search**:
   - Update `search_memory` method
   - Add RRF combination
   - Add feature flag

4. **Create Knowledge Base**:
   - Set up in Azure Portal
   - Connect data sources
   - Test document ingestion

5. **Test & Validate**:
   - Run test cases
   - Measure performance
   - Document findings

---

## Summary

**Foundry IQ POC** will:
- ✅ Add enterprise document search via Azure AI Search
- ✅ Integrate with Engram's tri-search using hybrid approach
- ✅ Provide broader knowledge coverage
- ✅ Maintain backward compatibility
- ✅ Enable gradual rollout via feature flag

**Strategy**: Hybrid approach - use Foundry IQ for enterprise documents, keep Engram tri-search for episodic memory and conversation history.

---

*Last Updated: January 2026*

