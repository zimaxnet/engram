# Background Tasks - User Context Guidelines

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Development Guidelines

---

## Overview

Background tasks in Engram must preserve user identity (`user_id`) throughout their execution to ensure:
- Proper user attribution for all operations
- Access control and data isolation
- Audit trail and compliance
- Enterprise boundaries (projects, departments)

---

## Critical Rules

### 1. Always Pass `user_id` Explicitly

**DO:**
```python
async def background_task(user_id: str, data: dict):
    logger.info(f"Background task started for user: {user_id}")
    # Use user_id explicitly
    await operation(user_id=user_id, data=data)
    logger.info(f"Background task completed for user: {user_id}")
```

**DON'T:**
```python
async def background_task(data: dict):
    # user_id not passed - will fail or use wrong user
    await operation(data=data)
```

### 2. Use Closures to Capture Context

**DO:**
```python
# Closure captures updated_context which contains user_id
async def _persist_with_timeout():
    user_id = updated_context.security.user_id  # Extract explicitly
    logger.info(f"Background task started for user: {user_id}")
    try:
        await persist_conversation(updated_context)
        logger.info(f"Background task completed for user: {user_id}")
    except Exception as e:
        logger.error(f"Background task failed for user: {user_id}: {e}")

asyncio.create_task(_persist_with_timeout())
```

**DON'T:**
```python
# Global state - loses user context
global_context = None

async def _persist_with_timeout():
    # May use wrong user_id if global_context changed
    await persist_conversation(global_context)
```

### 3. Log `user_id` at Start and Completion

**Pattern:**
```python
async def background_task(user_id: str, ...):
    logger.info(f"Background task started for user: {user_id}")
    try:
        # ... perform operations ...
        logger.info(f"Background task completed for user: {user_id}")
    except Exception as e:
        logger.error(f"Background task failed for user: {user_id}: {e}")
        raise
```

---

## Implementation Patterns

### Pattern 1: Explicit Parameter Passing

**Use Case:** FastAPI `BackgroundTasks` or function parameters

**Example:**
```python
# backend/api/routers/etl.py
@router.post("/ingest")
async def ingest_document(
    file: UploadFile,
    user: SecurityContext = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    user_id = user.user_id  # Extract from SecurityContext
    
    async def index_chunks(chunks: list, uid: str, filename: str):
        logger.info(f"Background task started: indexing chunks for user: {uid}")
        for chunk in chunks:
            await memory_client.add_fact(user_id=uid, fact=chunk["text"])
        logger.info(f"Background task completed: indexed chunks for user: {uid}")
    
    background_tasks.add_task(index_chunks, chunks, user_id, filename)
```

**Benefits:**
- Explicit user_id parameter
- Easy to test
- Clear function signature

### Pattern 2: Closure Capture

**Use Case:** `asyncio.create_task()` with context objects

**Example:**
```python
# backend/api/routers/chat.py
async def send_message(message: ChatMessage, user: SecurityContext = Depends(get_current_user)):
    # ... process message ...
    updated_context = ...  # Contains SecurityContext with user_id
    
    async def _persist_with_timeout():
        # Closure captures updated_context
        user_id = updated_context.security.user_id  # Extract explicitly
        logger.info(f"Background task started: persisting conversation for user: {user_id}")
        try:
            await persist_conversation(updated_context)
            logger.info(f"Background task completed: conversation persisted for user: {user_id}")
        except Exception as e:
            logger.error(f"Background task failed for user: {user_id}: {e}")
    
    asyncio.create_task(_persist_with_timeout())
```

**Benefits:**
- Captures full context object
- No parameter passing needed
- Works well with nested closures

### Pattern 3: Context Extraction

**Use Case:** When context object is available but needs explicit extraction

**Example:**
```python
# backend/api/routers/voice.py
async def voicelive_websocket(websocket: WebSocket, session_id: str):
    voice_context = EnterpriseContext(security=security, ...)
    
    async def _persist_latest_turns():
        # Extract user_id explicitly from context
        user_id = voice_context.security.user_id
        logger.info(f"Background task started: persisting voice conversation for user: {user_id}")
        try:
            await persist_conversation(voice_context)
            logger.info(f"Background task completed: voice conversation persisted for user: {user_id}")
        except Exception as e:
            logger.error(f"Background task failed for user: {user_id}: {e}")
    
    asyncio.create_task(_persist_latest_turns())
```

**Benefits:**
- Explicit user_id extraction
- Clear logging
- Easy debugging

---

## Common Pitfalls

### Pitfall 1: Global State

**BAD:**
```python
current_user_id = None

async def background_task():
    # Uses global - may be wrong user
    await operation(user_id=current_user_id)
```

**GOOD:**
```python
async def background_task(user_id: str):
    # Explicit parameter
    await operation(user_id=user_id)
```

### Pitfall 2: Missing User ID Extraction

**BAD:**
```python
async def _persist_with_timeout():
    # No user_id extraction - hard to debug
    await persist_conversation(updated_context)
```

**GOOD:**
```python
async def _persist_with_timeout():
    user_id = updated_context.security.user_id  # Extract explicitly
    logger.info(f"Background task started for user: {user_id}")
    await persist_conversation(updated_context)
    logger.info(f"Background task completed for user: {user_id}")
```

### Pitfall 3: Async Context Loss

**BAD:**
```python
# Context may be modified before task runs
asyncio.create_task(operation(context))
context = new_context  # Task may use new_context instead
```

**GOOD:**
```python
# Extract user_id immediately
user_id = context.security.user_id
asyncio.create_task(operation(user_id=user_id))
```

---

## Testing Background Tasks

### Test Pattern

```python
async def test_background_task_user_id():
    # Create test user
    user_id = "test-user-123"
    
    # Trigger background task
    await trigger_operation(user_id=user_id)
    
    # Wait for background task
    await asyncio.sleep(0.1)
    
    # Verify user_id was used
    logs = get_logs()
    assert f"Background task started for user: {user_id}" in logs
    assert f"Background task completed for user: {user_id}" in logs
    
    # Verify operations used correct user_id
    results = await get_operations(user_id=user_id)
    assert len(results) > 0
```

---

## Current Implementation Status

### ✅ Document Ingestion (`backend/api/routers/etl.py`)
- **Pattern:** Explicit parameter passing
- **Status:** ✅ Passes `user_id` explicitly to `index_chunks()`
- **Logging:** ✅ Added explicit user_id logging

### ✅ Chat Persistence (`backend/api/routers/chat.py`)
- **Pattern:** Closure capture
- **Status:** ✅ Captures `updated_context` with `user_id`
- **Logging:** ✅ Added explicit user_id logging

### ✅ Voice Persistence (`backend/api/routers/voice.py`)
- **Pattern:** Closure capture
- **Status:** ✅ Captures `voice_context` with `user_id`
- **Logging:** ✅ Added explicit user_id logging

---

## Checklist for New Background Tasks

When creating a new background task, ensure:

- [ ] `user_id` is passed explicitly as a parameter OR captured in closure
- [ ] `user_id` is extracted explicitly at task start
- [ ] `user_id` is logged at task start
- [ ] `user_id` is logged at task completion
- [ ] `user_id` is logged on error
- [ ] All operations within task use the correct `user_id`
- [ ] No global state is used for user context
- [ ] Task is testable with explicit `user_id`

---

## Related Documents

- `docs/architecture/user-identity-flow-comprehensive.md` - Complete user identity flow
- `docs/architecture/user-identity-fixes-required.md` - Gap analysis and fixes
- `docs/architecture/user-identity-summary.md` - Executive summary

---

**Key Takeaway:** Always extract and log `user_id` explicitly in background tasks. Never rely on global state or implicit context.

