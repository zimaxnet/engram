# User Identity Flow - Executive Summary

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Architecture Reference

---

## Quick Reference: User Identity Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER IDENTITY FLOW                           │
└─────────────────────────────────────────────────────────────────┘

1. FRONTEND AUTHENTICATION
   User Login (Google/Entra External ID)
     ↓
   MSAL acquires JWT token
     ↓
   Token stored: Local Storage
     ↓
   All API requests: Authorization: Bearer {token}

2. BACKEND AUTHENTICATION
   get_current_user() extracts token
     ↓
   EntraIDAuth.validate_token()
     ↓
   SecurityContext created:
     - user_id = token.oid (Object ID) ⭐ CRITICAL
     - tenant_id = token.tid
     - email, display_name, roles

3. ZEP MEMORY OPERATIONS
   get_or_create_user(user_id) ⭐ Must match SecurityContext.user_id
     ↓
   get_or_create_session(user_id, ...)
     ↓
   All memory operations use user_id:
     - add_fact(user_id, ...)
     - search_memory(user_id, ...) ⭐ Now filters by user
     - get_facts(user_id, ...)

4. TEMPORAL WORKFLOWS
   execute_agent_turn(user_id, tenant_id, ...)
     ↓
   Workflow receives user_id
     ↓
   Activities use user_id for all operations

5. DOCUMENT INGESTION
   POST /api/v1/etl/ingest
     ↓
   SecurityContext.user_id extracted
     ↓
   ingestion_service.ingest_document(user_id, ...)
     ↓
   Chunks indexed as facts with user_id

6. DATABASE OPERATIONS
   All queries filtered by user_id:
     - GET /api/v1/users/{user_id}/facts
     - GET /api/v1/sessions?user_id={user_id}
     - Search operations filter by user_id
```

---

## Critical Consistency Rule

**ALL systems MUST use the same `user_id`:**

```
token.oid (Entra ID)
  = SecurityContext.user_id
  = Zep User.user_id
  = Zep Session.user_id
  = Temporal Workflow.user_id
  = Document Ingestion.user_id
  = Search Operations.user_id
```

**Format:** UUID (e.g., `d240186f-f80e-4369-9296-57fef571cd93`)  
**Source:** `token.oid` from Entra ID JWT  
**Immutable:** Never changes for a user

---

## Component-Specific Requirements

### Frontend
- ✅ Acquires JWT token via MSAL
- ✅ Attaches token to all API requests
- ✅ Token includes `oid` (Object ID) as user identifier

### Backend API
- ✅ Validates JWT token
- ✅ Extracts `user_id = token.oid`
- ✅ Creates `SecurityContext` with user identity
- ✅ All endpoints receive `SecurityContext` via `get_current_user()`

### Zep Memory
- ✅ Users created with `user_id = SecurityContext.user_id`
- ✅ Sessions created with `user_id` reference
- ✅ Facts stored with `user_id` attribution
- ✅ Search operations filter by `user_id` ⭐ FIXED

### Temporal Workflows
- ✅ Workflows receive `user_id` and `tenant_id` as input
- ✅ Activities use `user_id` for all operations
- ✅ Context initialized with `user_id`

### Document Ingestion
- ✅ Documents attributed to `SecurityContext.user_id`
- ✅ Chunks indexed as facts with `user_id`
- ✅ MCP tools accept `user_id` parameter ⭐ FIXED

### Database/Search
- ✅ Facts queried by `user_id`: `/api/v1/users/{user_id}/facts`
- ✅ Sessions filtered by `user_id`: `?user_id={user_id}`
- ✅ Search operations filter by `user_id` ⭐ FIXED

---

## Recent Fixes (December 31, 2025)

### ✅ Fixed: Search Memory User Filtering
- `search_memory()` now accepts `user_id` parameter
- Sessions filtered by `user_id` before searching
- `enrich_context()` passes `user_id` to search

### ✅ Fixed: MCP Document Ingestion
- `ingest_document()` now accepts `user_id` parameter
- Falls back to system user with warning if not provided
- Documentation updated with user_id requirement

### ✅ Fixed: CORS Error Responses
- Error responses now include CORS headers
- Browser can read actual error messages
- Fixes "CORS policy" errors masking real issues

---

## Remaining Gaps

### ⚠️ Voice WebSocket Authentication
**Status:** Documented, needs implementation  
**Issue:** WebSockets cannot send Authorization headers  
**Required:** Extract token from query parameter or cookie

### ⚠️ MCP Tools User Attribution
**Status:** Partially fixed (ingest_document), others need update  
**Issue:** Some MCP tools still use hardcoded `user_id="mcp-user"`  
**Required:** Add `user_id` parameter to all MCP tools

### ⚠️ Background Task Context
**Status:** Documented, needs validation  
**Issue:** Background tasks may lose user context  
**Required:** Ensure `user_id` preserved in all async operations

---

## Testing Checklist

- [ ] Chat session uses correct `user_id`
- [ ] Document ingestion attributed to user
- [ ] Search only returns user's own data
- [ ] Temporal workflows use correct `user_id`
- [ ] Voice sessions attributed to user (when implemented)
- [ ] MCP operations attributed to user (when fixed)
- [ ] Cross-user data isolation verified

---

## Related Documents

- `docs/architecture/user-identity-flow-comprehensive.md` - Complete flow analysis
- `docs/architecture/user-identity-fixes-required.md` - Action items
- `docs/architecture/security-context-enterprise-architecture.md` - SecurityContext details
- `docs/4-layer-context-schema-story.md` - Original context schema

---

**Key Takeaway:** User identity flows from `token.oid` through `SecurityContext.user_id` to all downstream systems. Consistency is critical for access control, attribution, and enterprise boundaries.

