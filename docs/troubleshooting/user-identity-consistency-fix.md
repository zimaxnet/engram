# User Identity Consistency Fix

## Status: ✅ FIXED

**Date**: 2025-12-31  
**Issue**: Users must be consistent across all systems for enterprise boundaries

## Problem Statement

As documented in `docs/4-layer-context-schema-story.md`, the 4-layer context schema requires **consistent user identity** across all systems:

- Chat sessions
- Voice sessions  
- Episodes
- Semantic search
- Keyword search
- Graph knowledge

This is **critical for enterprise boundaries** (projects, departments). Users accessing the system need to be the same user throughout all systems.

## Root Cause

When `AUTH_REQUIRED=false`, the system was using `poc-user` which didn't exist in Zep. The code had retry logic that would create sessions **without user_id** (anonymous sessions), breaking user identity consistency.

**Error**:
```
Zep API error: 400 - POST https://zep.engram.work/api/v1/sessions 
bad request: user does not exist with user_id: poc-user
```

The code would then retry without `user_id`, creating anonymous sessions that break the enterprise boundary model.

## Solution

### 1. Added `get_or_create_user` Method

**File**: `backend/memory/client.py`

```python
async def get_or_create_user(self, user_id: str, metadata: dict = None) -> dict:
    """
    Get or create a user in Zep.
    
    CRITICAL: Users must exist in Zep before creating sessions.
    This ensures consistent user identity across all systems.
    """
```

This method:
- Checks if user exists in Zep
- Creates user if doesn't exist
- Includes metadata (email, display_name, tenant_id)

### 2. Updated `get_or_create_session` to Ensure User Exists

**File**: `backend/memory/client.py`

**Before**: Would retry session creation without `user_id` if user didn't exist  
**After**: Ensures user exists in Zep **before** creating session

```python
# CRITICAL: Ensure user exists in Zep first
user_metadata = {
    "tenant_id": metadata.get("tenant_id"),
    "email": metadata.get("email"),
    "display_name": metadata.get("display_name"),
}
await self.get_or_create_user(user_id, metadata=user_metadata)
```

### 3. Updated `enrich_context` to Pass User Metadata

**File**: `backend/memory/client.py`

Now passes full user metadata (email, display_name) from SecurityContext:

```python
session_metadata = {
    "tenant_id": context.security.tenant_id,
}
if context.security.email:
    session_metadata["email"] = context.security.email
if context.security.display_name:
    session_metadata["display_name"] = context.security.display_name
```

## Impact

### ✅ Fixed

1. **User Identity Consistency**: Users are created in Zep before sessions, ensuring consistent identity
2. **Enterprise Boundaries**: Same user_id flows through chat, voice, episodes, memory search
3. **No Anonymous Sessions**: Removed the fallback that created sessions without user_id

### 🔄 Behavior Change

**Before**:
- Session creation would fail if user didn't exist
- Code would retry without user_id (anonymous session)
- User identity was inconsistent

**After**:
- User is created in Zep if doesn't exist
- Session creation always includes user_id
- User identity is consistent across all systems

## Testing

1. **Test with AUTH_REQUIRED=false**:
   - User `poc-user` should be created in Zep automatically
   - Sessions should be created with `user_id=poc-user`
   - No "user does not exist" errors

2. **Test with AUTH_REQUIRED=true**:
   - Real users from Entra ID should be created in Zep
   - Sessions should use the actual user_id from token
   - User metadata (email, display_name) should be preserved

3. **Verify Enterprise Boundaries**:
   - Users from different tenants should be isolated
   - Memory search should respect user_id boundaries
   - Episodes should be scoped to correct user

## Related Files

- `backend/memory/client.py` - User and session creation
- `backend/api/middleware/auth.py` - SecurityContext creation
- `docs/4-layer-context-schema-story.md` - Architecture documentation

## References

- **4-Layer Context Schema**: `docs/4-layer-context-schema-story.md`
- **Layer 1 (Security)**: Ensures consistent user identity
- **Zep API**: `/api/v1/users` for user creation

---

**Status**: ✅ Implemented - Users are now created in Zep before sessions, ensuring consistent identity across all systems.

