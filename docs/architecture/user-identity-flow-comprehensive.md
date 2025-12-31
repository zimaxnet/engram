# Comprehensive User Identity Flow Architecture

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Classification:** Enterprise Architecture  
**Status:** Analysis & Design

---

## Executive Summary

This document provides a comprehensive analysis of how authenticated user identity flows through all Engram platform components, ensuring consistent user attribution, access control, and data isolation across:

1. **Frontend Authentication** (MSAL/Entra External ID)
2. **Backend API** (JWT validation & SecurityContext)
3. **Zep Memory** (Episodic & Semantic memory)
4. **Temporal Workflows** (Durable execution)
5. **Database Operations** (Keywords, Semantic Search, Knowledge Graph)
6. **Document Ingestion** (Unstructured document processing)

---

## 1. Frontend → Backend Authentication Flow

### 1.1 Frontend Token Acquisition

**Location:** `frontend/src/auth/authConfig.ts`, `frontend/src/services/api.ts`

**Flow:**
```
User Login (Google/Entra External ID)
  ↓
MSAL acquires JWT token
  ↓
Token stored in browser (Local Storage)
  ↓
Frontend API client adds token to requests:
  Authorization: Bearer {JWT_TOKEN}
```

**Key Code:**
```typescript
// frontend/src/services/api.ts
private async getAuthToken(): Promise<string | null> {
  return await getAccessToken() // MSAL token acquisition
}

// All API requests include token
headers['Authorization'] = `Bearer ${token}`
```

### 1.2 Backend Token Validation

**Location:** `backend/api/middleware/auth.py`

**Flow:**
```
Request arrives with Authorization header
  ↓
get_current_user() dependency extracts token
  ↓
EntraIDAuth.validate_token() validates JWT
  ↓
Extracts user identity from token:
  - user_id = token.oid (Object ID)
  - tenant_id = token.tid (Tenant ID)
  - email = token.email
  - display_name = token.name
  ↓
Creates SecurityContext with user identity
```

**Key Code:**
```python
# backend/api/middleware/auth.py
async def get_current_user(...) -> SecurityContext:
    token = await auth.validate_token(credentials.credentials)
    return SecurityContext(
        user_id=token.oid,  # CRITICAL: Object ID from Entra ID
        tenant_id=token.tid,
        email=token.email,
        display_name=token.name,
        roles=auth.map_roles(token.roles),
        scopes=auth.extract_scopes(token),
    )
```

**Critical Point:** `user_id` is extracted from `token.oid` (Object ID), which is the **unique, immutable identifier** for the user in Entra ID.

---

## 2. Backend → Zep Memory Flow

### 2.1 User Creation in Zep

**Location:** `backend/memory/client.py`

**Flow:**
```
SecurityContext created (with user_id from token.oid)
  ↓
Any memory operation requires session
  ↓
get_or_create_session() called
  ↓
get_or_create_user() ensures user exists in Zep FIRST
  ↓
User created in Zep with:
  - user_id: token.oid (matches SecurityContext.user_id)
  - metadata: {tenant_id, email, display_name}
  ↓
Session created with user_id reference
```

**Key Code:**
```python
# backend/memory/client.py
async def get_or_create_user(self, user_id: str, metadata: dict = None) -> dict:
    """
    CRITICAL: Users must exist in Zep before creating sessions.
    This ensures consistent user identity across:
    - Chat sessions
    - Voice sessions
    - Episodes
    - Semantic search
    - Keyword search
    - Graph knowledge
    """
    # Try to get existing user first
    result = await self._request("GET", f"/api/v1/users/{user_id}")
    if result:
        return result
    
    # Create new user
    payload = {
        "user_id": user_id,  # token.oid from SecurityContext
        "metadata": metadata or {}
    }
    return await self._request("POST", "/api/v1/users", json=payload)
```

**Critical Point:** The `user_id` passed to Zep **MUST** match `SecurityContext.user_id` (which comes from `token.oid`). This ensures:
- All sessions belong to the correct user
- All memory searches are scoped to the user
- All facts/entities are attributed to the user

### 2.2 Session Creation

**Location:** `backend/memory/client.py::get_or_create_session()`

**Flow:**
```
get_or_create_session(session_id, user_id, metadata)
  ↓
1. Ensure user exists (get_or_create_user)
  ↓
2. Try to get existing session
  ↓
3. Create new session if not exists:
   {
     "session_id": session_id,
     "user_id": user_id,  # From SecurityContext.user_id
     "metadata": {
       "tenant_id": context.security.tenant_id,
       "email": context.security.email,
       "display_name": context.security.display_name,
       "agent_id": ...,
       ...
     }
   }
```

**Critical Point:** Session metadata includes user identity information for proper attribution and filtering.

---

## 3. Chat & Voice Session Flow

### 3.1 Chat Endpoint

**Location:** `backend/api/routers/chat.py`

**Flow:**
```
POST /api/v1/chat
  ↓
get_current_user() → SecurityContext (user_id from token.oid)
  ↓
get_or_create_session(session_id, user) → EnterpriseContext
  ↓
enrich_context(context, query) → Calls Zep with user_id
  ↓
agent_chat(query, context, agent_id) → Uses context.security.user_id
  ↓
persist_conversation(context) → Saves to Zep with user_id
```

**Key Code:**
```python
# backend/api/routers/chat.py
@router.post("")
async def send_message(message: ChatMessage, user: SecurityContext = Depends(get_current_user)):
    session_id = message.session_id or str(uuid.uuid4())
    context = get_or_create_session(session_id, user)  # user.user_id used
    
    # Memory enrichment uses context.security.user_id
    context = await enrich_context(context, message.content)
    
    # Agent execution uses context
    response_text, updated_context, agent_id = await agent_chat(...)
    
    # Persistence uses context.security.user_id
    await persist_conversation(updated_context)
```

### 3.2 Voice Endpoint

**Location:** `backend/api/routers/voice.py`

**Flow:**
```
WebSocket /api/v1/voice/voicelive/{session_id}
  ↓
If AUTH_REQUIRED=false: Uses POC user
If AUTH_REQUIRED=true: Should extract user from token (TODO: Verify)
  ↓
Creates session with user_id
  ↓
Voice transcripts persisted to Zep with user_id
```

**Current Issue:** Voice WebSocket may not properly extract user identity when `AUTH_REQUIRED=true`. WebSockets cannot send custom headers, so token must come from:
- Query parameter: `?token={JWT}`
- Cookie: `auth_token={JWT}`
- Or use session-based auth

---

## 4. Temporal Workflow Flow

### 4.1 Workflow Input

**Location:** `backend/workflows/client.py`, `backend/workflows/agent_workflow.py`

**Flow:**
```
API endpoint receives request with SecurityContext
  ↓
execute_agent_turn() called with:
  - user_id: SecurityContext.user_id (token.oid)
  - tenant_id: SecurityContext.tenant_id (token.tid)
  - session_id: session identifier
  ↓
Temporal workflow started with AgentWorkflowInput:
  {
    "user_id": user_id,  # From SecurityContext
    "tenant_id": tenant_id,
    "session_id": session_id,
    "agent_id": agent_id,
    "user_message": message
  }
  ↓
Workflow activities receive user_id for all operations
```

**Key Code:**
```python
# backend/workflows/client.py
async def execute_agent_turn(
    user_id: str,  # From SecurityContext.user_id
    tenant_id: str,  # From SecurityContext.tenant_id
    session_id: str,
    agent_id: str,
    user_message: str,
) -> AgentWorkflowOutput:
    handle = await client.start_workflow(
        AgentWorkflow.run,
        AgentWorkflowInput(
            user_id=user_id,  # CRITICAL: Must match SecurityContext.user_id
            tenant_id=tenant_id,
            session_id=session_id,
            agent_id=agent_id,
            user_message=user_message,
        ),
        ...
    )
```

### 4.2 Workflow Activities

**Location:** `backend/workflows/activities.py`

**Flow:**
```
initialize_context_activity(user_id, tenant_id, session_id, agent_id)
  ↓
Creates SecurityContext with user_id
  ↓
Creates EnterpriseContext with SecurityContext
  ↓
All subsequent activities use context.security.user_id
  ↓
Memory operations (enrich, persist) use user_id
```

**Key Code:**
```python
# backend/workflows/activities.py
@activity.defn
async def initialize_context_activity(user_id: str, tenant_id: str, ...) -> str:
    security = SecurityContext(
        user_id=user_id,  # From workflow input
        tenant_id=tenant_id,
        ...
    )
    context = EnterpriseContext(security=security)
    return context.model_dump_json()
```

**Critical Point:** Workflow activities must use the `user_id` from workflow input, which comes from `SecurityContext.user_id` (token.oid).

---

## 5. Database Operations & Search

### 5.1 Semantic Search (Facts/Knowledge Graph)

**Location:** `backend/memory/client.py`

**Flow:**
```
Search request with SecurityContext
  ↓
get_facts(user_id=context.security.user_id, query=query)
  ↓
Zep API: GET /api/v1/users/{user_id}/facts?query={query}
  ↓
Returns facts scoped to user_id
```

**Key Code:**
```python
# backend/memory/client.py
async def get_facts(self, user_id: str, query: Optional[str] = None, limit: int = 20):
    # CRITICAL: user_id filters facts to this user only
    result = await self._request("GET", f"/api/v1/users/{user_id}/facts", params=params)
```

### 5.2 Keyword Search

**Location:** `backend/memory/client.py::search_memory()`

**Flow:**
```
Search request with SecurityContext
  ↓
search_memory(session_id, query, limit)
  ↓
Searches across sessions for the user
  ↓
Zep API filters by user_id implicitly (sessions belong to users)
```

**Current Implementation:** Keyword search searches across all sessions. Should be filtered by user_id.

**Gap:** `search_memory()` doesn't explicitly filter by `user_id`. It searches by `session_id`, but should also filter sessions by user.

### 5.3 Episodic Memory (Sessions)

**Location:** `backend/memory/client.py::list_sessions()`

**Flow:**
```
List episodes request with SecurityContext
  ↓
list_sessions(user_id=context.security.user_id, limit, offset)
  ↓
Zep API: GET /api/v1/sessions?user_id={user_id}&limit={limit}&offset={offset}
  ↓
Returns sessions scoped to user_id
```

**Key Code:**
```python
# backend/memory/client.py
async def list_sessions(self, user_id: Optional[str] = None, ...):
    if user_id:
        params["user_id"] = user_id  # CRITICAL: Filters by user
    result = await self._request("GET", "/api/v1/sessions", params=params)
```

---

## 6. Document Ingestion Flow

### 6.1 Document Upload Endpoint

**Location:** `backend/api/routers/etl.py`

**Flow:**
```
POST /api/v1/etl/ingest
  ↓
get_current_user() → SecurityContext (user_id from token.oid)
  ↓
File uploaded
  ↓
ingestion_service.ingest_document(
    content=content,
    filename=filename,
    content_type=content_type,
    user_id=user.user_id,  # CRITICAL: From SecurityContext
    background_tasks=background_tasks
)
  ↓
Document processed and chunked
  ↓
Chunks indexed to Zep as facts with user_id
```

**Key Code:**
```python
# backend/api/routers/etl.py
@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    user: SecurityContext = Depends(get_current_user),
):
    return await ingestion_service.ingest_document(
        content=content,
        filename=filename,
        content_type=content_type,
        user_id=user.user_id,  # From SecurityContext.user_id
        background_tasks=background_tasks
    )
```

### 6.2 Fact Creation

**Location:** `backend/etl/ingestion_service.py`

**Flow:**
```
ingest_document(user_id, ...)
  ↓
Document chunked into text pieces
  ↓
Background task: index_chunks(chunks, user_id, filename)
  ↓
For each chunk:
  memory_client.add_fact(
    user_id=user_id,  # CRITICAL: From SecurityContext
    fact=chunk["text"],
    metadata={
      "source": "document_upload",
      "filename": filename,
      ...
    }
  )
  ↓
Zep API: POST /api/v1/users/{user_id}/facts
  ↓
Fact stored with user_id attribution
```

**Key Code:**
```python
# backend/etl/ingestion_service.py
async def index_chunks(chunks_to_index: list, uid: str, fname: str):
    for chunk in chunks_to_index:
        await memory_client.add_fact(
            user_id=uid,  # From SecurityContext.user_id
            fact=chunk["text"],
            metadata={
                "source": "document_upload",
                "filename": fname,
                ...
            },
        )
```

**Critical Point:** All ingested documents are attributed to the authenticated user via `user_id`.

---

## 7. User Identity Consistency Requirements

### 7.1 Critical Consistency Points

**ALL systems MUST use the same `user_id`:**

1. **SecurityContext.user_id** = `token.oid` (from Entra ID JWT)
2. **Zep User.user_id** = `SecurityContext.user_id`
3. **Zep Session.user_id** = `SecurityContext.user_id`
4. **Temporal Workflow.user_id** = `SecurityContext.user_id`
5. **Document Ingestion.user_id** = `SecurityContext.user_id`
6. **Search Operations.user_id** = `SecurityContext.user_id`

### 7.2 User ID Format

**Standard:** `token.oid` (Object ID from Entra ID)
- Format: UUID (e.g., `d240186f-f80e-4369-9296-57fef571cd93`)
- Immutable: Never changes for a user
- Unique: Globally unique across all tenants
- Consistent: Same value in all Entra ID tokens for the user

### 7.3 Current Gaps & Issues

#### Gap 1: Voice WebSocket Authentication
**Issue:** WebSocket connections cannot send Authorization headers.  
**Current:** Uses POC user when `AUTH_REQUIRED=false`.  
**Required:** Token must come from query parameter or cookie.

#### Gap 2: MCP Document Ingestion
**Location:** `backend/api/routers/mcp_server.py::ingest_document()`

**Issue:** Uses hardcoded `user_id="system-ingestion"` instead of authenticated user.

**Current Code:**
```python
await client.get_or_create_session(
    session_id=doc_session_id,
    user_id="system-ingestion",  # ❌ HARDCODED - Should use authenticated user
    metadata={...}
)
```

**Required:** MCP tools should receive `SecurityContext` or `user_id` parameter.

#### Gap 3: Search Memory User Filtering
**Location:** `backend/memory/client.py::search_memory()`

**Issue:** `search_memory()` searches by `session_id` but doesn't explicitly filter by `user_id`. Should ensure sessions belong to the user.

**Current:** Searches all sessions matching the query.  
**Required:** Filter sessions by `user_id` before searching.

#### Gap 4: Background Tasks User Context
**Issue:** Background tasks (like document indexing) may lose user context.

**Current:** `user_id` is passed explicitly to background tasks.  
**Required:** Ensure background tasks maintain user context throughout execution.

---

## 8. Enterprise Boundaries & Access Control

### 8.1 Tenant Isolation

**All operations MUST respect tenant boundaries:**

```python
# SecurityContext provides tenant isolation
context.security.tenant_id  # From token.tid

# Zep operations filter by tenant
session_metadata["tenant_id"] = context.security.tenant_id

# Search operations should filter by tenant
# (Currently implemented via user_id, but should be explicit)
```

### 8.2 Project/Department Boundaries

**Future Requirement:** When project/department boundaries are implemented:

```python
# SecurityContext should include project/department
context.security.project_id: Optional[str]
context.security.department_id: Optional[str]

# Memory operations filter by project/department
memory_filter = {
    "user_id": context.security.user_id,
    "tenant_id": context.security.tenant_id,
    "project_id": context.security.project_id,  # Future
    "department_id": context.security.department_id,  # Future
}
```

### 8.3 Agent Attribution

**All agent actions MUST be attributed to the user:**

```python
# When agent performs actions, they're attributed to user
session_metadata["agent_id"] = agent_id
session_metadata["user_id"] = user_id  # User who initiated

# Workflow activities use user_id for all operations
activity_result = await some_activity(user_id=user_id, ...)
```

---

## 9. Data Flow Diagrams

### 9.1 Complete User Identity Flow

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ 1. User logs in (Google/Entra)
       │ 2. MSAL acquires JWT token
       │ 3. Token stored in Local Storage
       │
       │ 4. API request with Authorization: Bearer {token}
       ▼
┌─────────────────────┐
│   Backend API       │
│  (FastAPI)          │
└──────┬──────────────┘
       │ 5. get_current_user() extracts token
       │ 6. EntraIDAuth.validate_token()
       │ 7. Creates SecurityContext:
       │    - user_id = token.oid
       │    - tenant_id = token.tid
       │    - email, display_name, roles
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│   Zep Memory     │              │ Temporal Workflow│
│                  │              │                  │
│ get_or_create_   │              │ execute_agent_   │
│   user(user_id)  │              │   turn(user_id)  │
│                  │              │                  │
│ get_or_create_   │              │ Workflow receives│
│   session(       │              │ user_id, tenant_ │
│     user_id)    │              │   id             │
│                  │              │                  │
│ add_fact(       │              │ Activities use   │
│   user_id)      │              │ user_id for all  │
│                  │              │ operations       │
│ search_memory(   │              │                  │
│   user_id)      │              │                  │
└──────────────────┘              └──────────────────┘
       │                                     │
       │                                     │
       └─────────────────────────────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │  Document        │
            │  Ingestion       │
            │                  │
            │ ingest_document( │
            │   user_id)      │
            │                  │
            │ Chunks indexed   │
            │ as facts with    │
            │ user_id          │
            └──────────────────┘
```

### 9.2 User ID Consistency Chain

```
Entra ID JWT Token
  │
  ├─ token.oid (Object ID)
  │    │
  │    ▼
  │ SecurityContext.user_id
  │    │
  │    ├─► Zep User.user_id
  │    │
  │    ├─► Zep Session.user_id
  │    │
  │    ├─► Temporal Workflow.user_id
  │    │
  │    ├─► Document Ingestion.user_id
  │    │
  │    └─► Search Operations.user_id
  │
  └─ token.tid (Tenant ID)
       │
       ▼
  SecurityContext.tenant_id
       │
       ├─► Zep Session.metadata.tenant_id
       │
       └─► Temporal Workflow.tenant_id
```

---

## 10. Recommendations & Action Items

### 10.1 Immediate Fixes Required

1. **Fix MCP Document Ingestion**
   - Remove hardcoded `user_id="system-ingestion"`
   - Pass authenticated `user_id` to MCP tools
   - Update `ingest_document` MCP tool to accept `user_id` parameter

2. **Enhance Search Memory User Filtering**
   - Update `search_memory()` to explicitly filter by `user_id`
   - Ensure sessions belong to the user before searching
   - Add `user_id` parameter to `search_memory()` method

3. **Fix Voice WebSocket Authentication**
   - Implement token extraction from query parameter or cookie
   - Update WebSocket handler to validate token and extract user_id
   - Ensure voice sessions are created with authenticated user_id

### 10.2 Future Enhancements

1. **Project/Department Boundaries**
   - Add `project_id` and `department_id` to `SecurityContext`
   - Update memory operations to filter by project/department
   - Implement RBAC for project/department access

2. **Background Task Context Preservation**
   - Implement context propagation for background tasks
   - Ensure user_id is preserved throughout async operations
   - Add logging to track user context in background tasks

3. **Audit Logging**
   - Log all operations with user_id attribution
   - Track user actions across all systems
   - Implement audit trail for compliance

---

## 11. Testing & Validation

### 11.1 User Identity Consistency Tests

**Test 1: Chat Session User Attribution**
```python
# Verify chat session uses correct user_id
1. User logs in → Get token.oid
2. Send chat message
3. Verify Zep session created with user_id = token.oid
4. Verify session metadata includes user email/name
```

**Test 2: Document Ingestion User Attribution**
```python
# Verify ingested documents attributed to user
1. User logs in → Get token.oid
2. Upload document
3. Verify facts created with user_id = token.oid
4. Verify metadata includes user information
```

**Test 3: Search User Scoping**
```python
# Verify search only returns user's data
1. User A logs in → Ingest document A
2. User B logs in → Ingest document B
3. User A searches → Should only see document A
4. User B searches → Should only see document B
```

**Test 4: Temporal Workflow User Attribution**
```python
# Verify workflow uses correct user_id
1. User logs in → Get token.oid
2. Trigger workflow
3. Verify workflow input includes user_id = token.oid
4. Verify workflow activities use user_id
```

---

## 12. Conclusion

The Engram platform has a **mostly consistent** user identity flow, with the following key points:

✅ **Strengths:**
- Frontend properly acquires and sends JWT tokens
- Backend correctly extracts `user_id` from `token.oid`
- Zep memory operations use `user_id` consistently
- Document ingestion attributes documents to users
- Temporal workflows receive `user_id` as input

⚠️ **Gaps:**
- MCP document ingestion uses hardcoded user_id
- Voice WebSocket authentication needs improvement
- Search memory should explicitly filter by user_id
- Background tasks need context preservation

🔧 **Required Actions:**
1. Fix MCP document ingestion to use authenticated user
2. Enhance search memory to filter by user_id
3. Implement proper WebSocket authentication
4. Add comprehensive user identity consistency tests

---

## Appendix: Key Files Reference

| Component | File | Key Function |
|-----------|------|--------------|
| Frontend Auth | `frontend/src/auth/authConfig.ts` | Token acquisition |
| Frontend API | `frontend/src/services/api.ts` | Token attachment |
| Backend Auth | `backend/api/middleware/auth.py` | Token validation, SecurityContext creation |
| Zep Memory | `backend/memory/client.py` | User/session creation, search, facts |
| Temporal | `backend/workflows/client.py` | Workflow execution with user_id |
| Document Ingestion | `backend/api/routers/etl.py` | Document upload with user_id |
| Chat | `backend/api/routers/chat.py` | Chat with user context |
| Voice | `backend/api/routers/voice.py` | Voice with user context |

---

**Next Steps:**
1. Review and approve this architecture document
2. Implement fixes for identified gaps
3. Add comprehensive tests for user identity consistency
4. Update documentation with user identity requirements

