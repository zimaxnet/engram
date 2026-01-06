---
layout: default
title: Agent & User Isolation with Project-Based Access Control
parent: Architecture
nav_order: 1
---

# Agent & User Isolation with Project-Based Access Control

> **Implemented**: January 2026  
> **Purpose**: Ensure each agent has separate conversation threads, users only see their own data, and project-based collaboration is supported.

---

## Overview

Engram now implements **complete isolation** at three levels:

1. **Agent Isolation**: Elena, Marcus, and Sage each maintain separate conversation threads
2. **User Isolation**: Users only see their own conversations and data
3. **Project-Based Access**: Users can collaborate on shared projects when granted access

This architecture enables agents to validate each other's work while maintaining strict data boundaries.

---

## Architecture Changes

### 1. Composite Session Keys

**Before**: Single session ID shared across all agents  
**After**: Composite keys that include user, agent, and optional project

**Format**: `{user_id}:{agent_id}:{project_id?}:{session_id}`

**Example**:
- Elena's session: `user-123:elena:project-alpha:session-abc`
- Marcus's session: `user-123:marcus:project-alpha:session-def`
- Sage's session: `user-123:sage:project-alpha:session-ghi`

**Benefits**:
- Each agent maintains its own conversation history
- Agents can reference each other's work without mixing contexts
- Users can switch between agents without losing conversation state

### 2. SecurityContext Enhancements

**Added Field**: `project_id: Optional[str]`

```python
class SecurityContext(BaseModel):
    user_id: str
    tenant_id: str
    project_id: Optional[str]  # NEW: For project-based access
    roles: list[Role]
    scopes: list[str]
    # ... other fields
```

**New Method**: `can_access_project(project_id: str) -> bool`

Rules:
- Admins can access any project
- Users can access their own project (project_id matches)
- Users can access projects they have scope for (`project-{id}:read` or `project-{id}:write`)

### 3. Memory Filtering

**Updated**: All memory queries now filter by:
- `user_id` (required) - User isolation
- `tenant_id` (required) - Tenant isolation  
- `project_id` (optional) - Project-based access when specified

**Example**:
```python
# User's own sessions (no project restriction)
sessions = await list_episodes(user_id="user-123")

# Project-specific sessions
sessions = await list_episodes(user_id="user-123", project_id="project-alpha")

# Cross-project access (if user has scope)
if user.can_access_project("project-beta"):
    sessions = await list_episodes(user_id="user-123", project_id="project-beta")
```

---

## Frontend Changes

### Agent-Specific Sessions

**Before**: Single `sessionId` shared across all agents  
**After**: Separate `sessionIds` per agent stored in `sessionStorage`

**Implementation**:
```typescript
// Each agent has its own session ID
const sessionIds = {
  elena: 'session-elena-...',
  marcus: 'session-marcus-...',
  sage: 'session-sage-...'
}

// Get current session for active agent
const sessionId = sessionIds[activeAgent]
```

**Storage Keys**:
- `engram_session_elena`
- `engram_session_marcus`
- `engram_session_sage`

**Benefits**:
- Switching agents doesn't lose conversation history
- Each agent maintains its own context
- Users can have parallel conversations with different agents

---

## Backend Changes

### Session Management

**Function**: `get_or_create_session(session_id, security, agent_id)`

**Key Changes**:
- Requires `agent_id` parameter
- Creates composite session key internally
- Stores agent_id in context metadata

**Session Storage**:
```python
# Internal storage uses composite keys
_sessions = {
    "user-123:elena:project-alpha:session-abc": EnterpriseContext(...),
    "user-123:marcus:project-alpha:session-def": EnterpriseContext(...),
    "user-123:sage:project-alpha:session-ghi": EnterpriseContext(...),
}
```

### Memory Persistence

**Zep Session Metadata** now includes:
- `agent_id` - Which agent participated
- `project_id` - Which project (if specified)
- `user_id` - User attribution
- `tenant_id` - Tenant isolation

**Example Metadata**:
```json
{
  "agent_id": "elena",
  "project_id": "project-alpha",
  "tenant_id": "contoso-corp",
  "user_id": "user-123",
  "turn_count": 5,
  "summary": "Discussion about requirements..."
}
```

---

## Use Cases

### 1. Agent Validation

**Scenario**: Elena creates requirements, Marcus validates them

**Flow**:
1. User chats with Elena → Session: `user-123:elena:project-alpha:session-1`
2. Elena creates requirements document
3. User switches to Marcus → Session: `user-123:marcus:project-alpha:session-2`
4. Marcus can reference Elena's work via memory search (same project)
5. Marcus validates requirements in his own session

**Result**: Both agents maintain separate contexts but can access shared project data

### 2. Multi-User Project Collaboration

**Scenario**: Sarah and John work on Project Alpha

**Flow**:
1. Sarah's SecurityContext: `project_id="project-alpha"`, `scopes=["project-alpha:read", "project-alpha:write"]`
2. John's SecurityContext: `project_id="project-alpha"`, `scopes=["project-alpha:read"]`
3. Both can see Project Alpha sessions
4. Sarah can write, John can only read

**Result**: Project-based collaboration with role-based permissions

### 3. User Isolation

**Scenario**: Sarah works on Project Alpha, John works on Project Beta

**Flow**:
1. Sarah's sessions: Filtered by `user_id="sarah"` + `project_id="project-alpha"`
2. John's sessions: Filtered by `user_id="john"` + `project_id="project-beta"`
3. Neither sees the other's data

**Result**: Complete user isolation unless sharing a project

---

## API Changes

### Chat Endpoint

**Before**:
```python
POST /api/v1/chat
{
  "content": "Hello",
  "agent_id": "elena",
  "session_id": "session-123"
}
```

**After**: Same API, but backend creates agent-specific session internally

**Session Key**: `{user_id}:{agent_id}:{project_id?}:{session_id}`

### Episodes Endpoint

**Before**:
```python
GET /api/v1/memory/episodes?limit=20
# Returns all user's episodes
```

**After**:
```python
GET /api/v1/memory/episodes?limit=20
# Automatically filters by:
# - user_id (from SecurityContext)
# - project_id (from SecurityContext.project_id, if set)
```

### Clear Session Endpoint

**Before**:
```python
DELETE /api/v1/chat/session/{session_id}
# Clears session for all agents
```

**After**:
```python
DELETE /api/v1/chat/session/{session_id}?agent_id=elena
# Clears session for specific agent only
```

---

## Migration Notes

### Existing Sessions

**Legacy sessions** (without agent_id in key) will continue to work but:
- Will be treated as "elena" sessions by default
- Should migrate to new format over time

### Frontend Migration

**No breaking changes** - frontend automatically creates separate sessions per agent on first use.

### Backend Migration

**No database migration required** - session keys are in-memory only. Zep sessions already include agent_id in metadata.

---

## Security Guarantees

### 1. User Isolation

✅ **Enforced**: All queries filter by `user_id` from `SecurityContext`  
✅ **Verified**: Memory client requires `user_id` parameter  
✅ **Audited**: All sessions include user attribution in metadata

### 2. Agent Isolation

✅ **Enforced**: Composite session keys include `agent_id`  
✅ **Verified**: Each agent gets separate session storage  
✅ **Audited**: Agent ID stored in context and Zep metadata

### 3. Project-Based Access

✅ **Enforced**: `can_access_project()` method validates access  
✅ **Verified**: Memory queries filter by `project_id` when specified  
✅ **Audited**: Project ID stored in session metadata

### 4. Tenant Isolation

✅ **Enforced**: All queries filter by `tenant_id`  
✅ **Verified**: SecurityContext includes tenant_id from token  
✅ **Audited**: Tenant ID stored in all session metadata

---

## Testing

### Manual Testing

1. **Agent Isolation**:
   - Chat with Elena → Switch to Marcus → Verify separate conversations
   - Check that each agent maintains its own history

2. **User Isolation**:
   - Login as User A → Create sessions
   - Login as User B → Verify User A's sessions are not visible

3. **Project Access**:
   - User with `project-alpha:read` scope → Can see project-alpha sessions
   - User without scope → Cannot see project-alpha sessions

### Automated Testing

```python
# Test agent isolation
def test_agent_isolation():
    session1 = get_or_create_session("session-1", user, agent_id="elena")
    session2 = get_or_create_session("session-1", user, agent_id="marcus")
    assert session1 != session2  # Different sessions

# Test project access
def test_project_access():
    user.project_id = "project-alpha"
    assert user.can_access_project("project-alpha")  # Own project
    assert not user.can_access_project("project-beta")  # Different project
```

---

## Related Documentation

- [Security Context Flow](../01-architecture/user-identity-flow-comprehensive.md)
- [Memory Architecture](../concept/memory-architecture.md)
- [RBAC Middleware](../../backend/api/middleware/rbac.py)

---

*Last Updated: January 2026*

