---
layout: default
title: "User Identity Testing Summary"
parent: "Developer Guide"
---

# User Identity Testing Summary

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Test Documentation

---

## Overview

This document provides a summary of all test scripts and documentation created for validating user identity consistency across the Engram platform.

---

## Test Scripts Created

### 1. Voice WebSocket Authentication Test

**Script:** `scripts/test-voice-websocket-auth.py`

**Purpose:** Tests that voice WebSocket endpoint properly extracts and validates JWT tokens from query parameters.

**Usage:**
```bash
# With token
python3 scripts/test-voice-websocket-auth.py --token <JWT_TOKEN>

# Test without token (should fail if AUTH_REQUIRED=true)
python3 scripts/test-voice-websocket-auth.py --test-no-token
```

**Documentation:** `docs/testing/voice-websocket-auth-test.md`

---

### 2. MCP Tools User ID Attribution Test

**Script:** `scripts/test-mcp-tools-user-id.py`

**Purpose:** Tests that MCP tools properly receive and use `user_id` from agent context.

**Usage:**
```bash
# Test all tools
python3 scripts/test-mcp-tools-user-id.py --user-id <USER_ID>

# Test specific tool
python3 scripts/test-mcp-tools-user-id.py --user-id <USER_ID> --tool chat
```

**Documentation:** `docs/testing/mcp-tools-user-id-test.md`

---

### 3. Background Tasks User ID Preservation Test

**Script:** `scripts/test-background-tasks-user-id.py`

**Purpose:** Tests that background tasks properly preserve `user_id` throughout execution.

**Usage:**
```bash
# Test all background tasks
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID>

# Test specific background task
python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID> --test chat
```

**Documentation:** `docs/testing/background-tasks-user-id-test.md`

---

## Quick Test Guide

### Prerequisites

1. **Get JWT Token:**
   ```bash
   # From browser DevTools > Application > Local Storage
   # Find: msal.{CLIENT_ID}.idtoken
   export AUTH_TOKEN='your-jwt-token-here'
   ```

2. **Get User ID:**
   ```bash
   # Extract from token (token.oid) or use test user
   export TEST_USER_ID='d240186f-f80e-4369-9296-57fef571cd93'
   ```

### Run All Tests

```bash
# 1. Voice WebSocket Authentication
python3 scripts/test-voice-websocket-auth.py --token $AUTH_TOKEN

# 2. MCP Tools User ID Attribution
python3 scripts/test-mcp-tools-user-id.py --user-id $TEST_USER_ID

# 3. Background Tasks User ID Preservation
python3 scripts/test-background-tasks-user-id.py --user-id $TEST_USER_ID
```

---

## Test Coverage

### ✅ Voice WebSocket Authentication
- [x] WebSocket connection with valid token
- [x] WebSocket connection without token (should fail)
- [x] WebSocket connection with invalid token (should fail)
- [x] User ID extraction from token
- [x] SecurityContext creation with authenticated user

### ✅ MCP Tools User ID Attribution
- [x] Tool accepts `user_id` parameter
- [x] Tool uses provided `user_id` (not fallback)
- [x] Tool falls back correctly when `user_id` not provided
- [x] Agent injects `user_id` from context
- [x] Tool schema inspection for `user_id` field

### ✅ Background Tasks User ID Preservation
- [x] Chat persistence preserves `user_id`
- [x] Document ingestion preserves `user_id`
- [x] Voice persistence preserves `user_id`
- [x] Background task logging includes `user_id`
- [x] No user_id loss in async operations

---

## Expected Test Results

### Voice WebSocket Authentication

**Success:**
```
✅ WebSocket connection established
✅ Test message sent
✅ Received response
```

**Failure (no token):**
```
❌ WebSocket closed with code 1008: Authentication required
```

### MCP Tools User ID Attribution

**Success:**
```
✅ chat_with_agent result: ...
✅ enrich_memory result: Memory enriched successfully.
✅ search_memory result: ...
```

**Warning (no user_id):**
```
WARNING: chat_with_agent called without user_id - using fallback
```

### Background Tasks User ID Preservation

**Success:**
```
Background task started: persisting conversation for user: test-user-123
Background task completed: conversation persisted for user: test-user-123
✅ Chat persistence preserved user_id correctly
```

---

## Backend Log Verification

All tests should produce logs showing user_id:

**Voice WebSocket:**
```
INFO: VoiceLive WebSocket: Authenticated user {user_id} for session {session_id}
```

**MCP Tools:**
```
INFO: chat_with_agent called with user_id: {user_id}
DEBUG: Injected user_id={user_id} into tool chat_with_agent
```

**Background Tasks:**
```
INFO: Background task started: persisting conversation for user: {user_id}
INFO: Background task completed: conversation persisted for user: {user_id}
```

---

## Troubleshooting

### Common Issues

1. **Token Expired**
   - Get fresh token from browser
   - Tokens expire after 1 hour

2. **User ID Mismatch**
   - Verify token contains correct `oid` claim
   - Check backend logs for actual user_id used

3. **Background Task Not Running**
   - Check if task is fire-and-forget (may complete after test)
   - Wait a few seconds and check logs

4. **Import Errors**
   - Ensure backend dependencies are installed
   - Run from project root directory

---

## Related Documentation

- `docs/architecture/user-identity-flow-comprehensive.md` - Complete user identity flow
- `docs/architecture/user-identity-fixes-required.md` - Implementation details
- `docs/development/background-tasks-guidelines.md` - Background task patterns
- `docs/testing/voice-websocket-auth-test.md` - Voice WebSocket test details
- `docs/testing/mcp-tools-user-id-test.md` - MCP tools test details
- `docs/testing/background-tasks-user-id-test.md` - Background tasks test details

---

## Next Steps

1. **Run Tests:** Execute all test scripts to validate implementation
2. **Review Logs:** Check backend logs for user_id in all operations
3. **Verify Zep:** Check Zep memory for correct user_id attribution
4. **Monitor Production:** Watch logs in production for user_id consistency

---

**Key Takeaway:** All test scripts validate that `user_id` flows correctly from authentication through all system components, ensuring proper user attribution and access control.

