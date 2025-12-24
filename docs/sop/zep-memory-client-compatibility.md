# Zep Memory Client Method Compatibility

> **Issue ID**: ZEP-001  
> **Date**: December 24, 2025  
> **Status**: Resolved ✅

## Issue Summary

Story generation via Temporal workflows failed at the memory enrichment step with:

```
Memory enrichment failed: 'ZepMemoryClient' object has no attribute 'add_session'
```

## Symptoms

- Story generation workflow completed steps 1-3 successfully
- Step 4 (Enrich Zep memory) failed with AttributeError
- Story content was generated and saved but not persisted to memory
- Worker logs showed:

  ```
  Starting story workflow: story-ad164660033c
  Step 1: Generating story with Claude...
  Story generated: 14335 chars
  Step 3: Saving artifacts to docs folder...
  Artifacts saved: docs/stories/20251224-020303-temporal-success-story.md
  Step 4: Enriching Zep memory...
  Memory enrichment failed: 'ZepMemoryClient' object has no attribute 'add_session'
  ```

## Root Cause

**API Method Mismatch**: The activity code was calling methods that didn't exist on the `ZepMemoryClient`:

| Called By Activities | Actual Method in Client |
|---------------------|------------------------|
| `add_session()` | `get_or_create_session()` |
| `add_messages()` | `add_memory()` |

The story activities (`story_activities.py`) were written expecting these methods:

```python
# story_activities.py (lines 236-254)
await memory_client.add_session(
    session_id=session_id,
    user_id=input.user_id,
    metadata={...}
)

await memory_client.add_messages(
    session_id=session_id,
    messages=[{...}]
)
```

But `ZepMemoryClient` was refactored and these method names were changed without updating the callers.

## Solution

Added alias methods to `backend/memory/client.py`:

```python
async def add_session(
    self, session_id: str, user_id: str, metadata: dict = None
) -> dict:
    """
    Add/create a new session. Alias for get_or_create_session().
    
    Used by story_activities.py for memory enrichment.
    """
    return await self.get_or_create_session(
        session_id=session_id,
        user_id=user_id,
        metadata=metadata,
    )

async def add_messages(
    self, session_id: str, messages: list[dict]
) -> None:
    """
    Add messages to a session. Alias for add_memory().
    
    Used by story_activities.py for memory enrichment.
    """
    await self.add_memory(
        session_id=session_id,
        messages=messages,
    )
```

## Files Affected

| File | Issue |
|------|-------|
| `backend/memory/client.py` | Missing methods (fixed) |
| `backend/workflows/story_activities.py` | Calls `add_session()`, `add_messages()` |
| `backend/agents/sage/agent.py` | Calls `add_session()` |
| `backend/api/routers/story.py` | Calls `add_session()` |

## Prevention

1. **Interface Contracts**: When refactoring shared services, check for all callers
2. **Grep Before Rename**: `grep -r "method_name" backend/` before changing method names
3. **Type Hints**: Use Protocol/ABC types to enforce method signatures
4. **Integration Tests**: Add tests that exercise the full workflow path

## Verification

After deploying the fix, verify memory enrichment works:

```bash
# Create a story
curl -X POST https://engram.work/api/v1/story/create \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test Story", "include_diagram": false}'

# Check worker logs for success
az containerapp logs show --name staging-env-worker \
  --resource-group engram-rg --type console --tail 20 | grep -i "memory\|enriched"
```

Expected log:

```
Step 4: Enriching Zep memory...
Memory enriched: story-20251224-...
Story workflow completed
```

## Related

- [Temporal Azure Configuration](./temporal-azure-configuration.md) - Temporal setup guide
- [Zep Memory Architecture](../concept/memory-architecture.md) - Memory system design
