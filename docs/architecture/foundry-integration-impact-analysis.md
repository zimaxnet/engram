---
layout: default
title: Foundry Agent Service Integration - Impact Analysis
parent: Architecture
nav_order: 3
---

# Foundry Agent Service Integration - Impact Analysis

> **Status**: Impact Assessment  
> **Last Updated**: January 2026  
> **Purpose**: Clarify how Foundry integration affects existing working features

---

## Executive Summary

**✅ NO BREAKING CHANGES**: Foundry Agent Service integration is **ADDITIVE**, not a replacement. All existing features continue to work exactly as they do today.

**Key Principle**: Use Foundry for **NEW capabilities** (thread management, file storage) while **KEEPING** existing RAG, vector search, function calling, and document ingestion.

---

## Current Working Features (Unchanged)

### 1. RAG (Retrieval Augmented Generation) ✅

**Current Implementation**:
- Location: `backend/agents/base.py` → `_reason_node()`
- Uses: `memory_client.search_memory()` with **tri-search** (keyword + vector + graph)
- Storage: Zep with pgvector for semantic search
- Status: **WORKING** - No changes needed

**Impact**: **ZERO** - RAG continues to work exactly as before

**Code Reference**:
```python
# This code continues to work unchanged
results = await memory_client.search_memory(
    session_id="global-search",
    query=query,
    limit=5
)
```

**With Foundry**: RAG continues using Zep. Foundry doesn't replace this.

---

### 2. Unstructured File Ingestion ✅

**Current Implementation**:
- Location: `backend/etl/processor.py` and `backend/etl/ingestion_service.py`
- Uses: `unstructured` library for document processing
- Workflow: File → Unstructured partition → Chunking → Tri-indexing (keyword, vector, graph)
- Status: **WORKING** - Workflow exists, ready for testing

**Impact**: **ZERO** - Document ingestion continues to work

**Code Reference**:
```python
# This workflow continues unchanged
chunks = processor.process_file(content, filename, content_type)
await self._index_chunks_tri(chunks, user_id, filename, document_id, session_id, upload_timestamp)
```

**With Foundry**: 
- **Option A** (Recommended): Keep existing ingestion, use Foundry for file **storage** only
- **Option B**: Use Foundry file upload API for new uploads, but keep existing ingestion pipeline

**Decision**: Keep existing ingestion pipeline. Foundry file storage is **optional enhancement**.

---

### 3. Vector Stores ✅

**Current Implementation**:
- Location: `backend/memory/embedding_client.py` and Zep pgvector
- Uses: Azure OpenAI embeddings (`text-embedding-3-small`)
- Storage: Zep with pgvector for semantic similarity search
- Status: **WORKING** - Part of tri-search

**Impact**: **ZERO** - Vector search continues using Zep

**Code Reference**:
```python
# Vector embeddings continue to work
embedding = await embedding_client.generate_embedding(text)
# Stored in Zep pgvector, searched via memory_client.search_memory()
```

**With Foundry**: 
- **Keep Zep vectors** for episodic memory and conversation history
- **Optional**: Use Foundry vector stores for **document-only** semantic search (separate use case)

**Decision**: Keep Zep vectors. Foundry vectors are **optional** for document search only.

---

### 4. Function Calling (Tools) ✅

**Current Implementation**:
- Location: `backend/agents/*/agent.py` → `_maybe_use_tool()` methods
- Uses: LangChain tool decorators (`@tool`)
- Tools: `search_memory`, `send_email`, `create_user_story`, `assess_risks`, etc.
- Status: **WORKING** - Agents execute tools successfully

**Impact**: **ZERO** - Function calling continues to work

**Code Reference**:
```python
# Tool execution continues unchanged
tool_registry = {t.name: t for t in self.tools}
tool = tool_registry.get(tool_name)
result = await tool.ainvoke(tool_args)
```

**With Foundry**: 
- **Keep existing tool execution** (LangChain tools)
- **Optional**: Register tools with Foundry for **observability** only (doesn't change execution)

**Decision**: Keep existing tool execution. Foundry tool registration is **optional** for monitoring.

---

## What Foundry Adds (New Capabilities)

### 1. Thread Management (NEW)

**What It Does**: Provides managed conversation thread storage

**Current State**: In-memory `_sessions` dict in `chat.py`

**With Foundry**: 
- Threads stored in Foundry (Cosmos DB or managed)
- Persistent across restarts
- Project-based thread isolation

**Impact on Existing Code**: **MINIMAL**
- Replace `_sessions` dict with Foundry thread API calls
- `EnterpriseContext` continues to work (loads from Foundry thread)
- All agent logic unchanged

**Migration Path**:
```python
# BEFORE (current)
_sessions[session_key] = EnterpriseContext(...)

# AFTER (with Foundry)
thread_id = await foundry_client.create_thread(user_id, agent_id, project_id)
context = EnterpriseContext.from_foundry_thread(thread_id)
```

---

### 2. File Storage (NEW)

**What It Does**: Managed file storage with automatic indexing

**Current State**: Files stored in Blob Storage, processed by Unstructured

**With Foundry**: 
- Files stored in Foundry (Blob Storage managed)
- Automatic file indexing for RAG
- File-based tool calling

**Impact on Existing Code**: **MINIMAL**
- Keep existing Unstructured processing
- **Option**: Store processed files in Foundry for agent access
- Existing ingestion pipeline unchanged

**Migration Path**:
```python
# Keep existing ingestion
chunks = processor.process_file(content, filename, content_type)
await self._index_chunks_tri(chunks, ...)  # Still works

# Optional: Also store in Foundry for agent file access
if USE_FOUNDRY_FILES:
    await foundry_client.upload_file(thread_id, file_path)
```

---

### 3. Vector Stores (OPTIONAL)

**What It Does**: Managed Azure AI Search for document vectors

**Current State**: Zep pgvector for all vectors

**With Foundry**: 
- Separate vector store for documents only
- Managed Azure AI Search
- Automatic embedding generation

**Impact on Existing Code**: **ZERO** (if not used)
- Zep vectors continue to work
- Foundry vectors are **separate** use case (documents only)
- Can be enabled/disabled via feature flag

**Decision**: **Don't use Foundry vectors initially**. Keep Zep for everything.

---

### 4. Tool Infrastructure (OPTIONAL)

**What It Does**: Built-in tool calling framework

**Current State**: LangChain tools with custom execution

**With Foundry**: 
- Tool registration for observability
- Built-in tool validation

**Impact on Existing Code**: **ZERO** (if not used)
- Existing tool execution unchanged
- Foundry tool registration is **optional** for monitoring only

**Decision**: **Don't use Foundry tools initially**. Keep existing LangChain tools.

---

## Integration Strategy: Feature Flags

Use feature flags to enable Foundry features gradually without breaking existing functionality:

```python
# backend/core/config.py
USE_FOUNDRY_THREADS: bool = Field(False, alias="USE_FOUNDRY_THREADS")
USE_FOUNDRY_FILES: bool = Field(False, alias="USE_FOUNDRY_FILES")
USE_FOUNDRY_VECTORS: bool = Field(False, alias="USE_FOUNDRY_VECTORS")  # Not recommended initially
USE_FOUNDRY_TOOLS: bool = Field(False, alias="USE_FOUNDRY_TOOLS")  # Not recommended initially
```

**Default**: All `False` - Existing features work exactly as before.

---

## Migration Phases (Zero Downtime)

### Phase 1: POC (No Production Impact)

**Goal**: Test Foundry thread management

**Changes**:
- Add `FoundryAgentServiceClient` class
- Add feature flag `USE_FOUNDRY_THREADS=false` (default)
- Test in isolated environment

**Impact**: **ZERO** - Feature flag disabled, existing code unchanged

---

### Phase 2: Thread Management (Optional)

**Goal**: Replace in-memory sessions with Foundry threads

**Changes**:
- Update `get_or_create_session()` to use Foundry when flag enabled
- Keep fallback to in-memory sessions

**Impact**: **MINIMAL** - Only affects session storage, not agent logic

**Rollback**: Set `USE_FOUNDRY_THREADS=false` to revert instantly

---

### Phase 3: File Storage (Optional)

**Goal**: Use Foundry for file storage

**Changes**:
- Add Foundry file upload alongside existing ingestion
- Keep existing Unstructured processing

**Impact**: **MINIMAL** - Additive only, existing ingestion unchanged

**Rollback**: Set `USE_FOUNDRY_FILES=false` to revert instantly

---

## Code Examples: Zero-Impact Integration

### Example 1: RAG Continues Unchanged

```python
# backend/agents/base.py - NO CHANGES NEEDED
async def _reason_node(self, state: AgentState) -> AgentState:
    # This code works exactly as before
    results = await memory_client.search_memory(
        session_id="global-search",
        query=query,
        limit=5
    )
    # RAG injection continues to work
    memory_context = "\n\n## Retrieved Knowledge\n" + "\n\n".join(memory_items)
    # ... rest unchanged
```

**Foundry Impact**: None. RAG uses Zep, not Foundry.

---

### Example 2: Document Ingestion Continues Unchanged

```python
# backend/etl/ingestion_service.py - MINIMAL CHANGES
async def ingest_document(self, content: bytes, filename: str, ...):
    # Existing processing continues
    chunks = processor.process_file(content, filename, content_type)
    await self._index_chunks_tri(chunks, ...)  # Still works
    
    # Optional: Also store in Foundry (if flag enabled)
    if settings.USE_FOUNDRY_FILES:
        thread_id = await get_current_thread(user_id, agent_id)
        await foundry_client.upload_file(thread_id, file_path)
    
    return IngestResponse(...)
```

**Foundry Impact**: Additive only. Existing ingestion unchanged.

---

### Example 3: Function Calling Continues Unchanged

```python
# backend/agents/elena/agent.py - NO CHANGES NEEDED
async def _maybe_use_tool(self, state: AgentState) -> AgentState:
    # Existing tool execution continues
    tool_registry = {t.name: t for t in self.tools}
    tool = tool_registry.get(tool_name)
    result = await tool.ainvoke(tool_args)  # Still works
    
    # Optional: Log to Foundry (if flag enabled)
    if settings.USE_FOUNDRY_TOOLS:
        await foundry_client.log_tool_execution(thread_id, tool_name, result)
    
    return state
```

**Foundry Impact**: Optional logging only. Tool execution unchanged.

---

## Risk Mitigation

### Risk 1: Breaking Existing Features

**Mitigation**:
- ✅ Feature flags (all disabled by default)
- ✅ Gradual rollout (one feature at a time)
- ✅ Fallback to existing code paths
- ✅ Comprehensive testing before enabling flags

### Risk 2: Performance Impact

**Mitigation**:
- ✅ Foundry calls are async (non-blocking)
- ✅ Feature flags allow instant disable
- ✅ Monitor performance metrics
- ✅ Load testing before production

### Risk 3: Data Migration Complexity

**Mitigation**:
- ✅ No data migration needed (Foundry is additive)
- ✅ Existing Zep data continues to work
- ✅ Foundry threads are new, not replacing old data
- ✅ Can run both systems in parallel

---

## Testing Strategy

### Unit Tests

**Existing Tests**: Continue to pass (no changes to core logic)

**New Tests**: 
- Test Foundry client in isolation
- Test feature flag behavior
- Test fallback to existing code

### Integration Tests

**Existing Tests**: Continue to pass

**New Tests**:
- Test Foundry thread creation/retrieval
- Test RAG still works with Foundry threads
- Test document ingestion with Foundry files (optional)

### E2E Tests

**Existing Tests**: Continue to pass

**New Tests**:
- Test agent conversation with Foundry threads
- Test feature flag toggling
- Test rollback scenarios

---

## Summary: What Changes vs. What Stays

### ✅ STAYS THE SAME (No Changes)

1. **RAG Implementation** - Continues using Zep tri-search
2. **Vector Search** - Continues using Zep pgvector
3. **Function Calling** - Continues using LangChain tools
4. **Document Ingestion** - Continues using Unstructured
5. **Agent Logic** - All LangGraph logic unchanged
6. **Memory Search** - Continues using Zep `search_memory()`
7. **Tool Execution** - All tool execution unchanged

### 🆕 NEW (Additive Only)

1. **Thread Management** - Optional Foundry thread storage
2. **File Storage** - Optional Foundry file storage
3. **Observability** - Optional Foundry monitoring

### 🔄 MINIMAL CHANGES (Feature Flag Controlled)

1. **Session Storage** - Can use Foundry threads (optional)
2. **File Upload** - Can store in Foundry (optional)

---

## Recommendation

**Start with POC only**:
1. Create `FoundryAgentServiceClient` (isolated, no production impact)
2. Test thread management in development
3. **Keep all feature flags disabled** in production
4. Evaluate benefits before enabling any flags

**Gradual Adoption**:
- Enable `USE_FOUNDRY_THREADS` only after thorough testing
- Keep `USE_FOUNDRY_FILES` and `USE_FOUNDRY_VECTORS` disabled initially
- Monitor impact before enabling additional features

**Rollback Plan**:
- Set all feature flags to `false` to instantly revert
- No data migration needed (Foundry is additive)
- Existing features continue to work

---

## Conclusion

**✅ ZERO RISK TO EXISTING FEATURES**

Foundry Agent Service integration is:
- **Additive** - New capabilities, not replacements
- **Optional** - Feature flags control adoption
- **Reversible** - Instant rollback via flags
- **Non-Breaking** - All existing code continues to work

**Your existing features (RAG, vectors, function calling, ingestion) are safe and continue to work exactly as they do today.**

---

*Last Updated: January 2026*

