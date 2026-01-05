---
layout: default
title: "User Identity Fixes Required"
parent: "Architecture"
---

# User Identity Fixes Required

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Action Items

---

## Critical Issues Identified

### Issue 1: MCP Document Ingestion Uses Hardcoded User ID

**Location:** `backend/api/routers/mcp_server.py::ingest_document()`

**Problem:**
```python
# Current (WRONG):
await client.get_or_create_session(
    session_id=doc_session_id,
    user_id="system-ingestion",  # ❌ Hardcoded
    metadata={...}
)
```

**Impact:**
- All documents ingested via MCP are attributed to "system-ingestion"
- Users cannot see their own ingested documents
- Search results include documents from all users
- Violates user isolation and access control

**Fix Required:**
1. Add `user_id` parameter to `ingest_document` MCP tool
2. When called from agents (with context), extract `user_id` from `EnterpriseContext`
3. When called externally (MCP server), require `user_id` parameter or use authenticated context
4. Update all MCP tool calls to pass `user_id`

---

### Issue 2: Search Memory Doesn't Filter by User ID

**Location:** `backend/memory/client.py::search_memory()`

**Problem:**
```python
# Current:
async def search_memory(self, session_id: str, query: str, limit: int = 10):
    # Searches across ALL sessions, not filtered by user_id
    sessions_data = await self._request("GET", "/api/v1/sessions")
    # No user_id filtering
```

**Impact:**
- Search may return results from other users' sessions
- Violates user data isolation
- Security risk if sensitive data is in sessions

**Fix Required:**
1. Add `user_id` parameter to `search_memory()`
2. Filter sessions by `user_id` before searching
3. Update all callers to pass `user_id` from `SecurityContext`

---

### Issue 3: Voice WebSocket Authentication

**Location:** `backend/api/routers/voice.py::voicelive_websocket()`

**Problem:**
- WebSockets cannot send Authorization headers
- Currently uses POC user when `AUTH_REQUIRED=false`
- No mechanism to extract user identity when `AUTH_REQUIRED=true`

**Impact:**
- Voice sessions not attributed to authenticated users
- Voice transcripts not properly scoped to users
- Security risk if voice data is sensitive

**Fix Required:**
1. Extract token from WebSocket query parameter: `?token={JWT}`
2. Or use cookie-based authentication for WebSockets
3. Validate token and extract `user_id`
4. Create voice sessions with authenticated `user_id`

---

### Issue 4: MCP Tools Use Hardcoded User IDs

**Location:** `backend/api/routers/mcp_server.py`, `backend/api/routers/mcp.py`

**Problem:**
```python
# Multiple MCP tools use hardcoded user_id:
security = SecurityContext(
    user_id="mcp-user",  # ❌ Hardcoded
    tenant_id="mcp-tenant",
    ...
)
```

**Impact:**
- All MCP tool operations attributed to "mcp-user"
- No way to track which user initiated MCP operations
- Violates user attribution requirements

**Fix Required:**
1. MCP tools should accept `user_id` as parameter
2. When called from agents, extract `user_id` from `EnterpriseContext`
3. When called externally, require `user_id` parameter
4. Update all MCP tools to use authenticated `user_id`

---

## Implementation Plan

### Phase 1: Fix MCP Document Ingestion (Priority: HIGH)

**File:** `backend/api/routers/mcp_server.py`

**Changes:**
1. Add `user_id: Optional[str] = None` parameter to `ingest_document()`
2. If `user_id` is None, try to extract from context (if available)
3. If still None, use system user but log warning
4. Update tool signature and documentation

**Code:**
```python
@mcp_server.tool()
async def ingest_document(
    content: str,
    title: str,
    user_id: Optional[str] = None,  # NEW: Accept user_id
    doc_type: str = "markdown",
    topics: Optional[str] = None,
    agent_id: str = "elena",
    metadata: Optional[str] = None,
) -> str:
    # Use provided user_id or fallback to system
    actual_user_id = user_id or "system-ingestion"
    if not user_id:
        logger.warning("ingest_document called without user_id - using system user")
    
    await client.get_or_create_session(
        session_id=doc_session_id,
        user_id=actual_user_id,  # Use provided user_id
        metadata={...}
    )
```

---

### Phase 2: Fix Search Memory User Filtering (Priority: HIGH)

**File:** `backend/memory/client.py`

**Changes:**
1. Add `user_id: Optional[str] = None` parameter to `search_memory()`
2. Filter sessions by `user_id` before searching
3. Update `enrich_context()` to pass `user_id`

**Code:**
```python
async def search_memory(
    self,
    session_id: str,
    query: str,
    limit: int = 10,
    user_id: Optional[str] = None,  # NEW: Filter by user
    search_type: str = "similarity",
) -> list[dict]:
    # Filter sessions by user_id if provided
    params = {}
    if user_id:
        params["user_id"] = user_id
    
    sessions_data = await self._request("GET", "/api/v1/sessions", params=params)
    # Rest of search logic...
```

**Update Caller:**
```python
# backend/memory/client.py::enrich_context()
memory_results = await self.search_memory(
    session_id=session_id,
    query=query,
    limit=5,
    user_id=user_id,  # NEW: Pass user_id
)
```

---

### Phase 3: Fix Voice WebSocket Authentication (Priority: MEDIUM)

**File:** `backend/api/routers/voice.py`

**Changes:**
1. Extract token from query parameter: `?token={JWT}`
2. Validate token and extract `user_id`
3. Create voice sessions with authenticated `user_id`

**Code:**
```python
@router.websocket("/voicelive/{session_id}")
async def voicelive_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # Extract token from query parameter
    token = websocket.query_params.get("token")
    user_id = "poc-user"  # Default
    
    if token:
        try:
            auth = get_auth()
            token_payload = await auth.validate_token(token)
            user_id = token_payload.oid  # Authenticated user
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
    
    # Create session with user_id
    security = SecurityContext(
        user_id=user_id,
        tenant_id=...,
        ...
    )
```

---

### Phase 4: Fix MCP Tools User Attribution (Priority: MEDIUM)

**Files:** `backend/api/routers/mcp_server.py`, `backend/api/routers/mcp.py`

**Changes:**
1. Add `user_id` parameter to all MCP tools
2. Update tools to use provided `user_id`
3. Document that `user_id` should be provided when calling from agents

**Code:**
```python
@mcp_server.tool()
async def chat_with_agent(
    message: str,
    user_id: Optional[str] = None,  # NEW
    session_id: Optional[str] = None,
    agent_id: Optional[str] = "elena",
    ctx: Context = None
) -> str:
    # Use provided user_id or fallback
    actual_user_id = user_id or "mcp-user"
    
    security = SecurityContext(
        user_id=actual_user_id,  # Use provided user_id
        tenant_id="mcp-tenant",
        ...
    )
```

---

## Testing Requirements

### Test 1: MCP Document Ingestion User Attribution
```python
# Test that ingested documents are attributed to correct user
1. User A logs in → user_id = "user-a-oid"
2. Call ingest_document(user_id="user-a-oid", ...)
3. Verify Zep session created with user_id = "user-a-oid"
4. User B logs in → user_id = "user-b-oid"
5. Search for document → Should NOT see User A's document
```

### Test 2: Search Memory User Filtering
```python
# Test that search only returns user's own data
1. User A creates session A with data
2. User B creates session B with data
3. User A searches → Should only see session A results
4. User B searches → Should only see session B results
```

### Test 3: Voice WebSocket Authentication
```python
# Test that voice sessions use authenticated user
1. User logs in → Get token
2. Connect WebSocket with ?token={JWT}
3. Verify voice session created with user_id from token
4. Verify transcripts attributed to user
```

---

## Migration Notes

### Backward Compatibility

1. **MCP Tools:** Adding optional `user_id` parameter maintains backward compatibility
2. **Search Memory:** Adding optional `user_id` parameter maintains backward compatibility
3. **Voice WebSocket:** Token extraction is optional, falls back to POC user

### Breaking Changes

None - all changes are additive with fallbacks.

---

## Priority Order

1. **IMMEDIATE:** Fix MCP document ingestion (Issue 1)
2. **IMMEDIATE:** Fix search memory user filtering (Issue 2)
3. **HIGH:** Fix voice WebSocket authentication (Issue 3)
4. **MEDIUM:** Fix MCP tools user attribution (Issue 4)

---

## Success Criteria

✅ All document ingestion attributed to authenticated users  
✅ All search operations filtered by user_id  
✅ All voice sessions attributed to authenticated users  
✅ All MCP operations attributed to authenticated users  
✅ User identity consistent across all systems  
✅ No hardcoded user_ids in production code  
✅ Comprehensive tests validate user isolation

