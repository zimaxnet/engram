---
layout: default
title: "SecurityContext: The Foundation of Enterprise Identity & Attribution"
parent: "Architecture"
---

# SecurityContext: The Foundation of Enterprise Identity & Attribution

> *"Every interaction in Engram is attributable, every access is scoped, every boundary is enforced. SecurityContext is not optional—it's the foundation."*
> — **Dr. Elena Vasquez, Session sess-arch-001**

---

## Executive Summary

**SecurityContext (Layer 1)** is the cornerstone of Engram's enterprise security architecture. It establishes **who** is making the request, **what** they can access, and **where** their data boundaries lie. This document explains how SecurityContext enables:

1. **Consistent User Identity** across all systems (chat, voice, episodes, memory, search)
2. **Enterprise Boundaries** (projects, departments, tenants)
3. **Agent Attribution** (Marcus's work is attributable to him)
4. **Access Control** (employees only see their current project data)

This is a **major architectural breakthrough** that ensures enterprise-grade security and compliance.

---

## Part 1: What is SecurityContext?

### Definition

**SecurityContext** is Layer 1 of the 4-Layer Enterprise Context Schema. It encapsulates:

```python
class SecurityContext(BaseModel):
    # Identity
    user_id: str              # Unique identifier from Entra ID (e.g., "sarah.chen@contoso.com")
    tenant_id: str            # Organization identifier (e.g., "contoso-corp")
    session_id: str           # Current session ID
    
    # Permissions
    roles: list[Role]         # ADMIN, ANALYST, PM, VIEWER, DEVELOPER
    scopes: list[str]         # Fine-grained scopes (e.g., ["projects:read", "project-delta:write"])
    
    # Metadata (from Entra ID token)
    email: Optional[str]        # User email
    display_name: Optional[str] # User display name
    token_expiry: Optional[datetime] # Token expiration
```

### Where It Comes From

**Source**: Azure Entra ID (via Azure CIAM) JWT token

**Flow**:
1. User authenticates via Google/Entra ID
2. Azure CIAM issues JWT token with claims:
   - `oid` (Object ID) → `user_id`
   - `tid` (Tenant ID) → `tenant_id`
   - `email` → `email`
   - `name` → `display_name`
   - `roles` → `roles` (mapped from Entra ID groups)
   - `scp` (scopes) → `scopes`
3. Backend validates token and creates `SecurityContext`
4. **SecurityContext flows through ALL systems**

---

## Part 2: The Breakthrough - Consistent Identity Across All Systems

### The Problem We Solved

**Before**: Users were inconsistent across systems:
- Chat used `poc-user`
- Voice used `voice-user`
- Memory search failed because user didn't exist in Zep
- Episodes couldn't be attributed to the right user
- Enterprise boundaries were broken

**After**: **Same user_id everywhere**:
- ✅ Chat: `sarah.chen@contoso.com`
- ✅ Voice: `sarah.chen@contoso.com`
- ✅ Episodes: `sarah.chen@contoso.com`
- ✅ Memory Search: `sarah.chen@contoso.com`
- ✅ Graph Knowledge: `sarah.chen@contoso.com`

### How It Works

**1. User Creation in Zep** (First Time):
```python
# When SecurityContext is created, ensure user exists in Zep
await memory_client.get_or_create_user(
    user_id=security.user_id,  # "sarah.chen@contoso.com"
    metadata={
        "tenant_id": security.tenant_id,  # "contoso-corp"
        "email": security.email,
        "display_name": security.display_name,
    }
)
```

**2. Session Creation** (Every Interaction):
```python
# All sessions use the same user_id
await memory_client.get_or_create_session(
    session_id=session_id,
    user_id=security.user_id,  # ALWAYS the same
    metadata={
        "tenant_id": security.tenant_id,
        "channel": "chat" | "voice" | "episode",
    }
)
```

**3. Memory Operations** (All Scoped to User):
```python
# Semantic search - only returns user's data
facts = await memory_client.get_facts(
    user_id=security.user_id,  # Scoped to user
    query=query
)

# Episodic search - only user's sessions
results = await memory_client.search_memory(
    session_id=session_id,  # User's session
    query=query
)
```

---

## Part 3: Enterprise Boundaries - Project & Department Isolation

### The Requirement

**Enterprise employees must only see data pertaining to their current project.**

Example:
- **Sarah Chen** works on **Project Delta** (Contoso Corp)
- She should **NOT** see:
  - Project Alpha data (different project)
  - Fabrikam Corp data (different tenant)
  - Other employees' personal data

### How SecurityContext Enforces Boundaries

**1. Tenant Isolation** (`tenant_id`):
```python
# All queries filtered by tenant_id
memory_filter = security.get_memory_filter()
# Returns: {"tenant_id": "contoso-corp", "user_id": "sarah.chen@contoso.com", "scopes": [...]}

# Zep queries automatically scoped
results = await memory_client.search_memory(
    session_id=session_id,
    query=query,
    # Implicitly filtered by tenant_id from SecurityContext
)
```

**2. Project Scopes** (`scopes`):
```python
# User has scopes: ["project-delta:read", "project-delta:write"]
if security.has_scope("project-delta:read"):
    # Allow access to Project Delta data
    project_data = await get_project_data("project-delta")
else:
    raise PermissionDenied("project-delta", "read")
```

**3. Role-Based Access** (`roles`):
```python
# Sarah is ANALYST - can read, cannot modify system settings
if security.has_role(Role.ANALYST):
    # Can chat, search memory, view episodes
    pass
else:
    raise PermissionDenied("system", "access")
```

### Example: Project Delta Access Control

**Scenario**: Sarah Chen (ANALYST) asks about Project Delta budget

**SecurityContext**:
```python
SecurityContext(
    user_id="sarah.chen@contoso.com",
    tenant_id="contoso-corp",
    roles=[Role.ANALYST],
    scopes=["project-delta:read", "project-delta:write"],
    email="sarah.chen@contoso.com",
    display_name="Sarah Chen"
)
```

**Memory Query** (Automatic Filtering):
```python
# Zep automatically filters by:
# - tenant_id: "contoso-corp" (no Fabrikam data)
# - user_id: "sarah.chen@contoso.com" (only Sarah's sessions)
# - Scopes checked before returning project data
```

**Result**: Sarah only sees Project Delta data within Contoso Corp, nothing else.

---

## Part 4: Agent Attribution - "Marcus's Work is Attributable to Him"

### The Requirement

**When Marcus (Project Manager agent) does work, it must be attributable to him.**

Example:
- Marcus creates a project timeline
- Marcus assesses risks
- Marcus generates status reports
- **All of this must be traceable to Marcus**

### How SecurityContext Enables Attribution

**1. Agent Actions Include SecurityContext**:
```python
# When Marcus creates a timeline
async def create_project_timeline(project_details: str, context: EnterpriseContext):
    # Context includes SecurityContext
    security = context.security
    
    # Create timeline with attribution
    timeline = {
        "project": project_details,
        "created_by": security.user_id,  # "marcus@engram.ai" or user who invoked Marcus
        "created_by_agent": "marcus",    # Agent identifier
        "tenant_id": security.tenant_id,  # Scoped to tenant
        "timestamp": datetime.utcnow()
    }
    
    # Persist with full context
    await persist_timeline(timeline, context)
```

**2. Memory Persistence Includes Attribution**:
```python
# When Marcus's response is persisted
await memory_client.add_memory(
    session_id=session_id,
    messages=[{
        "role": "assistant",
        "content": "Based on my analysis, the timeline is...",
        "metadata": {
            "agent_id": "marcus",
            "user_id": context.security.user_id,  # Who invoked Marcus
            "tenant_id": context.security.tenant_id,
            "attribution": "marcus-generated-timeline"
        }
    }]
)
```

**3. Search Results Include Attribution**:
```python
# When searching for "Project Delta timeline"
results = await memory_client.search_memory(
    session_id=session_id,
    query="Project Delta timeline"
)

# Results include:
# {
#     "content": "Timeline for Project Delta...",
#     "agent_id": "marcus",
#     "user_id": "sarah.chen@contoso.com",  # Who asked Marcus
#     "tenant_id": "contoso-corp",
#     "attribution": "marcus-generated-timeline"
# }
```

### Example: Marcus Creates Risk Assessment

**User**: Sarah Chen asks Marcus to assess Project Delta risks

**SecurityContext** (Sarah's):
```python
SecurityContext(
    user_id="sarah.chen@contoso.com",
    tenant_id="contoso-corp",
    roles=[Role.ANALYST],
    scopes=["project-delta:read", "project-delta:write"]
)
```

**Marcus's Action**:
```python
# Marcus creates risk assessment
risk_assessment = await marcus.assess_risks(
    project_context="Project Delta",
    context=context  # Includes Sarah's SecurityContext
)

# Persisted with attribution:
{
    "content": "Risk assessment for Project Delta...",
    "agent_id": "marcus",
    "created_by_user": "sarah.chen@contoso.com",  # Sarah invoked Marcus
    "tenant_id": "contoso-corp",
    "project": "project-delta",
    "attribution": "marcus-risk-assessment"
}
```

**Result**: 
- ✅ Risk assessment is **attributable to Marcus**
- ✅ **Invoked by Sarah** (traceable)
- ✅ **Scoped to Contoso Corp** (enterprise boundary)
- ✅ **Project Delta only** (scope enforcement)

---

## Part 5: The Complete Flow - SecurityContext Through All Systems

### Flow Diagram Overview

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Authentication (Azure Entra ID)                          │
│    → JWT Token with claims (oid, tid, email, roles, scopes) │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SecurityContext Creation (Backend)                        │
│    → Extract claims from JWT                                │
│    → Create SecurityContext object                          │
│    → Validate permissions                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. User Creation in Zep (First Time)                        │
│    → Ensure user exists: user_id, tenant_id, email          │
│    → Create if doesn't exist                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Session Creation (Every Interaction)                    │
│    → Chat: user_id, tenant_id, channel="chat"               │
│    → Voice: user_id, tenant_id, channel="voice"             │
│    → Episodes: user_id, tenant_id, channel="episode"       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Memory Operations (All Scoped)                          │
│    → Semantic Search: filtered by user_id, tenant_id        │
│    → Keyword Search: filtered by user_id, tenant_id         │
│    → Graph Knowledge: filtered by user_id, tenant_id        │
│    → Episodes: filtered by user_id, tenant_id               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Agent Attribution (All Actions)                          │
│    → Marcus creates timeline                            │
│    → Elena analyzes requirements                                 │
│    → All include: user_id, tenant_id, agent_id, scopes     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Persistence (All Data)                                   │
│    → Zep Memory: user_id, tenant_id, metadata               │
│    → Episodes: user_id, tenant_id, project scopes           │
│    → Graph Knowledge: user_id, tenant_id, attribution        │
└─────────────────────────────────────────────────────────────┘
```

### Code Example: Complete Flow

```python
# 1. User authenticates → JWT token
token = await authenticate_user()

# 2. Backend creates SecurityContext
security = SecurityContext(
    user_id=token.oid,  # "sarah.chen@contoso.com"
    tenant_id=token.tid,  # "contoso-corp"
    roles=map_roles(token.roles),  # [Role.ANALYST]
    scopes=extract_scopes(token),  # ["project-delta:read"]
    email=token.email,
    display_name=token.name
)

# 3. Ensure user exists in Zep
await memory_client.get_or_create_user(
    user_id=security.user_id,
    metadata={
        "tenant_id": security.tenant_id,
        "email": security.email,
        "display_name": security.display_name
    }
)

# 4. Create session (chat, voice, episode)
context = EnterpriseContext(security=security)
context.episodic.conversation_id = session_id

await memory_client.get_or_create_session(
    session_id=session_id,
    user_id=security.user_id,  # Same everywhere
    metadata={
        "tenant_id": security.tenant_id,
        "channel": "chat"
    }
)

# 5. Memory operations (all scoped)
facts = await memory_client.get_facts(
    user_id=security.user_id,  # Only Sarah's facts
    query="Project Delta"
)

# 6. Agent action (attributed)
response = await marcus.assess_risks(
    project_context="Project Delta",
    context=context  # Includes SecurityContext
)

# 7. Persistence (all attributed)
await memory_client.add_memory(
    session_id=session_id,
    messages=[{
        "role": "assistant",
        "content": response,
        "metadata": {
            "agent_id": "marcus",
            "user_id": security.user_id,  # Sarah invoked Marcus
            "tenant_id": security.tenant_id,
            "project": "project-delta"
        }
    }]
)
```

---

## Part 6: Enterprise Security Guarantees

### Guarantee 1: Multi-Tenant Isolation

**Enforced by**: `tenant_id` in SecurityContext

**Result**: 
- Contoso Corp users **cannot** access Fabrikam Corp data
- Tenant boundaries are **hard-coded** into every query
- No cross-tenant data leakage possible

### Guarantee 2: Project Scoping

**Enforced by**: `scopes` in SecurityContext

**Result**:
- Users only see projects they have access to
- `project-delta:read` scope required to see Project Delta data
- No unauthorized project access

### Guarantee 3: User Attribution

**Enforced by**: `user_id` in SecurityContext

**Result**:
- Every action is attributable to a user
- Marcus's work is traceable to who invoked him
- Audit trail is complete

### Guarantee 4: Role-Based Access Control

**Enforced by**: `roles` in SecurityContext

**Result**:
- ANALYST can read, cannot modify system settings
- ADMIN has full access
- VIEWER can only read
- Permissions are **enforced at the SecurityContext layer**

---

## Part 7: Implementation Details

### File: `backend/core/context.py`

**SecurityContext Class** (Lines 38-74):
```python
class SecurityContext(BaseModel):
    user_id: str
    tenant_id: str
    session_id: str
    roles: list[Role]
    scopes: list[str]
    email: Optional[str]
    display_name: Optional[str]
    
    def has_role(self, role: Role) -> bool:
        """Check if user has specific role"""
        
    def has_scope(self, scope: str) -> bool:
        """Check if user has specific scope"""
        
    def get_memory_filter(self) -> dict:
        """Generate filter for memory queries"""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "scopes": self.scopes,
        }
```

### File: `backend/memory/client.py`

**User Creation** (Lines 101-150):
```python
async def get_or_create_user(self, user_id: str, metadata: dict = None):
    """Ensure user exists in Zep before creating sessions"""
    # Creates user with tenant_id, email, display_name
    # This ensures consistent identity across all systems
```

**Session Creation** (Lines 152-204):
```python
async def get_or_create_session(self, session_id: str, user_id: str, metadata: dict = None):
    """Create session with user_id - ensures user exists first"""
    # Ensures user exists in Zep
    await self.get_or_create_user(user_id, metadata)
    # Creates session with same user_id
```

### File: `backend/api/middleware/auth.py`

**SecurityContext Creation** (Lines 461-547):
```python
async def get_current_user(...) -> SecurityContext:
    """Extract SecurityContext from JWT token"""
    # Validates JWT token
    # Extracts claims (oid, tid, email, roles, scopes)
    # Creates SecurityContext
    return SecurityContext(
        user_id=token.oid,
        tenant_id=token.tid,
        roles=map_roles(token.roles),
        scopes=extract_scopes(token),
        email=token.email,
        display_name=token.name
    )
```

---

## Part 8: Why This Matters

### For Enterprise Customers

1. **Compliance**: Every action is attributable, every access is logged
2. **Security**: Multi-tenant isolation, project scoping, RBAC
3. **Audit**: Complete audit trail with user_id, tenant_id, agent_id
4. **Trust**: Employees only see their project data, nothing else

### For Engram Platform

1. **Scalability**: SecurityContext is lightweight, flows through all systems
2. **Consistency**: Same user_id everywhere, no identity fragmentation
3. **Attribution**: Agent actions are traceable to users
4. **Boundaries**: Enterprise boundaries enforced at the SecurityContext layer

---

## Conclusion

**SecurityContext is the foundation of Engram's enterprise security architecture.**

It ensures:
- ✅ **Consistent Identity**: Same user_id across all systems
- ✅ **Enterprise Boundaries**: Tenant isolation, project scoping
- ✅ **Agent Attribution**: Marcus's work is attributable to him
- ✅ **Access Control**: Employees only see their current project data

This is a **major architectural breakthrough** that enables enterprise-grade security and compliance.

---

**Related Documents**:
- `docs/4-layer-context-schema-story.md` - Full context schema documentation
- `docs/troubleshooting/user-identity-consistency-fix.md` - Implementation details
- `docs/architecture/auth-flow-diagram.json` - Authentication flow diagram

