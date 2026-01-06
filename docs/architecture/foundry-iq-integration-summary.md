---
layout: default
title: Foundry IQ Integration Summary
parent: Architecture
nav_order: 20
---

# Foundry IQ Integration Summary

> **Status**: ✅ POC Implementation Complete  
> **Date**: January 2026  
> **Feature**: Enterprise Document Search via Foundry IQ

---

## Overview

**Foundry IQ** integration is now implemented as a POC. This adds enterprise document search capabilities to Engram's existing tri-search, creating a **hybrid search** that combines:

- **Engram Tri-Search**: Episodic memory, conversation history, knowledge graph
- **Foundry IQ**: Enterprise documents, SharePoint, external knowledge bases

---

## Implementation

### 1. Foundry IQ Client ✅

**File**: `backend/agents/foundry_iq_client.py`

**Features**:
- REST API client for Foundry IQ knowledge base search
- Authentication via Managed Identity or API key
- Search method with filters and project scoping
- List and get knowledge base methods
- Graceful error handling

**Key Methods**:
- `search(query, limit, filters, project_id)` - Search knowledge base
- `list_knowledge_bases()` - List all knowledge bases
- `get_knowledge_base(kb_id)` - Get knowledge base info

### 2. Configuration ✅

**File**: `backend/core/config.py`

**Added**:
- `use_foundry_iq: bool` - Feature flag (default: False)
- `foundry_iq_knowledge_base_id: Optional[str]` - Knowledge base ID

**Environment Variables**:
- `USE_FOUNDRY_IQ=true` - Enable Foundry IQ
- `FOUNDRY_IQ_KB_ID=kb-...` - Knowledge base ID

### 3. Hybrid Search Integration ✅

**File**: `backend/memory/client.py`

**Updated**: `search_memory()` method

**Changes**:
- Added Foundry IQ as Phase 3 (after keyword search, before RRF)
- Integrated Foundry IQ results into RRF fusion
- Added `foundry_iq_rank` and `foundry_iq_score` to RRF scoring
- Updated `fusion_source` to include "foundry-iq"
- Enhanced logging to show Foundry IQ result counts

**Search Flow**:
```
1. Semantic Search (pgvector)
2. Keyword Search (Zep)
3. Foundry IQ Search (Azure AI Search) ← NEW
4. RRF Fusion (combines all three)
5. Return top results
```

### 4. Test Script ✅

**File**: `scripts/test_foundry_iq.py`

**Features**:
- Tests Foundry IQ client initialization
- Lists knowledge bases
- Gets knowledge base info
- Tests search with multiple queries
- Comprehensive error handling

---

## How It Works

### Hybrid Search Flow

```
User Query
    ↓
Phase 1: Semantic Search (pgvector)
    ↓
Phase 2: Keyword Search (Zep)
    ↓
Phase 3: Foundry IQ Search (Azure AI Search) ← NEW
    ↓
Phase 4: RRF Fusion
    ├── Score semantic results
    ├── Score keyword results
    ├── Score Foundry IQ results ← NEW
    └── Combine scores
    ↓
Final Results (sorted by RRF score)
```

### RRF Scoring

Foundry IQ results are integrated into RRF using the same formula:

```
RRF Score = Σ (1 / (k + rank_i))
```

Where:
- `k = 60` (standard RRF constant)
- `rank_i` = rank in each search method (semantic, keyword, foundry-iq)

**Example**:
- Semantic result at rank 1: `1 / (60 + 1) = 0.0164`
- Keyword result at rank 1: `1 / (60 + 1) = 0.0164`
- Foundry IQ result at rank 1: `1 / (60 + 1) = 0.0164`
- **Combined RRF score**: `0.0492` (if result appears in all three)

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

## Testing

### Test Script

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
source .venv/bin/activate
python3 scripts/test_foundry_iq.py
```

### Test Cases

1. **Client Initialization**:
   - ✅ Verify client creates successfully
   - ✅ Check configuration validation

2. **List Knowledge Bases**:
   - ✅ Verify API call succeeds
   - ✅ Check response format

3. **Get Knowledge Base**:
   - ✅ Verify knowledge base info retrieved
   - ✅ Check status and metadata

4. **Search**:
   - ✅ Test multiple queries
   - ✅ Verify results format
   - ✅ Check scoring

### Integration Testing

1. **Hybrid Search**:
   - Enable Foundry IQ
   - Run search via `memory_client.search_memory()`
   - Verify Foundry IQ results included
   - Check RRF fusion works correctly

2. **Fallback**:
   - Disable Foundry IQ
   - Verify Engram-only search works
   - No errors in logs

---

## Next Steps

### 1. Create Knowledge Base

**In Azure Portal**:
1. Navigate to: Azure AI Foundry → Project `zimax` → Knowledge Bases
2. Create new knowledge base
3. Connect data sources:
   - SharePoint sites
   - Fabric OneLake
   - Web content
4. Configure indexing
5. Get knowledge base ID

### 2. Configure Environment

**Set in Key Vault**:
- `foundry-iq-kb-id`: Knowledge base ID
- `foundry-iq-enabled`: `true`

**Or in `.env`** (for local testing):
```bash
USE_FOUNDRY_IQ=true
FOUNDRY_IQ_KB_ID=kb-...
```

### 3. Test Integration

1. Run test script: `python3 scripts/test_foundry_iq.py`
2. Test hybrid search via API
3. Verify results include Foundry IQ documents
4. Check RRF fusion quality

### 4. Monitor & Optimize

1. Monitor search latency
2. Compare result quality (Engram-only vs. hybrid)
3. Optimize RRF weights if needed
4. Tune knowledge base indexing

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

## Architecture

### Component Diagram

```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Hybrid Search (search_memory)     │
├─────────────────────────────────────┤
│  Phase 1: Semantic Search          │
│  Phase 2: Keyword Search            │
│  Phase 3: Foundry IQ Search ← NEW   │
│  Phase 4: RRF Fusion                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Final Results  │
└─────────────────┘
```

### Data Flow

```
Engram Tri-Search Results
    ↓
Foundry IQ Results
    ↓
RRF Fusion
    ↓
Combined Results (sorted by RRF score)
```

---

## Summary

✅ **Foundry IQ POC Implementation Complete**

**What's Done**:
- ✅ Foundry IQ client created
- ✅ Configuration added
- ✅ Hybrid search integrated
- ✅ RRF fusion updated
- ✅ Test script created
- ✅ Documentation written

**What's Next**:
1. Create knowledge base in Azure Portal
2. Configure knowledge base ID
3. Test with enterprise documents
4. Validate hybrid search quality

**Status**: Ready for knowledge base setup and testing.

---

*Last Updated: January 2026*

