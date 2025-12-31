# Background Tasks User ID Preservation Test

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Test Documentation

---

## Overview

This document describes how to test that background tasks properly preserve `user_id` throughout their execution, ensuring proper user attribution for all asynchronous operations.

---

## Test Requirements

1. **Backend Running**: API server must be running
2. **Zep Memory**: Zep memory service should be accessible
3. **Test User ID**: Valid user ID to test with (e.g., from `token.oid`)

---

## Test Scenarios

### Test 1: Chat Persistence Background Task

**Objective:** Verify that chat persistence background task preserves `user_id` from context.

**Steps:**
1. Send chat message through API
2. Verify background task logs include `user_id`
3. Check Zep memory for session with correct `user_id`

**Expected Result:**
- Background task logs: `"Background task started: persisting conversation for user: {user_id}"`
- Background task logs: `"Background task completed: conversation persisted for user: {user_id}"`
- Zep session created with correct `user_id`
- No user_id mismatch in logs

**Test Script:**
```bash
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID> --test chat
```

---

### Test 2: Document Ingestion Background Task

**Objective:** Verify that document ingestion background task preserves `user_id` parameter.

**Steps:**
1. Upload document through API
2. Verify background task receives `user_id`
3. Check Zep memory for facts with correct `user_id`

**Expected Result:**
- Background task logs: `"Background task started: indexing chunks for user: {user_id}"`
- Background task logs: `"Background task completed: indexed chunks for user: {user_id}"`
- Zep facts created with correct `user_id`
- All chunks attributed to correct user

**Test Script:**
```bash
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID> --test document
```

---

### Test 3: Voice Persistence Background Task

**Objective:** Verify that voice persistence background task preserves `user_id` from context.

**Steps:**
1. Connect to voice WebSocket with authenticated user
2. Send voice messages
3. Verify background task logs include `user_id`
4. Check Zep memory for voice session with correct `user_id`

**Expected Result:**
- Background task logs: `"Background task started: persisting voice conversation for user: {user_id}"`
- Background task logs: `"Background task completed: voice conversation persisted for user: {user_id}"`
- Zep session created with correct `user_id`
- Voice transcripts attributed to correct user

**Test Script:**
```bash
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID> --test voice
```

---

## Automated Testing

### Using Test Script

```bash
# Test all background tasks
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID>

# Test specific background task
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID> --test chat
```

### Expected Output

```
============================================================
Background Tasks User ID Preservation Test
============================================================
User ID: test-user-123
Test: all

Test 1: Chat Persistence Background Task
------------------------------------------------------------
Testing chat persistence with user_id: test-user-123
Background task started: persisting conversation for user: test-user-123
Background task completed: conversation persisted for user: test-user-123
✅ Chat persistence preserved user_id correctly

Test 2: Document Ingestion Background Task
------------------------------------------------------------
Testing document ingestion with user_id: test-user-123
✅ Document ingestion accepted with user_id

...

============================================================
Test Summary
============================================================
✅ chat: PASSED
✅ document: PASSED
✅ voice: PASSED

✅ All tests passed!
```

---

## Backend Log Verification

Check backend logs for user_id in background tasks:

**Chat Persistence:**
```
INFO: Background task started: persisting conversation for user: test-user-123
INFO: Background task completed: conversation persisted for user: test-user-123
```

**Document Ingestion:**
```
INFO: Background task started: indexing 5 chunks for user: test-user-123, file: test-document.md
INFO: Background task completed: indexed 5 chunks for user: test-user-123, file: test-document.md
```

**Voice Persistence:**
```
INFO: Background task started: persisting voice conversation for user: test-user-123
INFO: Background task completed: voice conversation persisted for user: test-user-123
```

---

## Manual Testing

### Test Chat Persistence

1. Send chat message through API
2. Check logs immediately after response
3. Wait for background task to complete
4. Verify logs show correct user_id

```bash
# Send chat message
curl -X POST https://api.engram.work/api/v1/chat \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test message",
    "agent_id": "elena",
    "session_id": "test-session"
  }'

# Check logs for background task messages
# Should see: "Background task started: persisting conversation for user: {user_id}"
```

### Test Document Ingestion

1. Upload document through API
2. Check logs for background task start
3. Wait for indexing to complete
4. Verify logs show correct user_id

```bash
# Upload document
curl -X POST https://api.engram.work/api/v1/etl/ingest \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -F "file=@test-document.md"

# Check logs for background task messages
# Should see: "Background task started: indexing chunks for user: {user_id}"
```

### Test Voice Persistence

1. Connect to voice WebSocket
2. Send voice messages
3. Check logs for background task messages
4. Verify user_id in logs

```bash
# Use test script from voice WebSocket test
python3 scripts/test-voice-websocket-auth.py --token $AUTH_TOKEN

# Check logs for background task messages
# Should see: "Background task started: persisting voice conversation for user: {user_id}"
```

---

## Troubleshooting

### Issue: Background task logs don't show user_id

**Possible Causes:**
- user_id not extracted explicitly in background task
- Closure not capturing context correctly
- Logging not added to background task

**Solutions:**
- Verify background task extracts `user_id` explicitly: `user_id = context.security.user_id`
- Check closure captures context object correctly
- Ensure logging statements include `user_id`

### Issue: Background task uses wrong user_id

**Possible Causes:**
- Global state being used
- Context object modified before task runs
- Multiple concurrent requests interfering

**Solutions:**
- Never use global state for user context
- Extract `user_id` immediately before creating task
- Verify closure captures context at creation time

### Issue: Background task fails silently

**Possible Causes:**
- Exception not logged with user_id
- Error handling doesn't include user_id
- Task not awaited (fire-and-forget)

**Solutions:**
- Ensure error logging includes `user_id`
- Add try/except with user_id in error message
- Consider awaiting critical background tasks

---

## Related Documentation

- `docs/development/background-tasks-guidelines.md` - Background task patterns
- `docs/architecture/user-identity-flow-comprehensive.md` - Complete user identity flow
- `backend/api/routers/chat.py` - Chat persistence implementation
- `backend/api/routers/voice.py` - Voice persistence implementation
- `backend/etl/ingestion_service.py` - Document ingestion implementation

