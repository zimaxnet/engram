# Voice WebSocket Authentication Test

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Test Documentation

---

## Overview

This document describes how to test the voice WebSocket authentication implementation that extracts and validates JWT tokens from query parameters.

---

## Test Requirements

1. **JWT Token**: Valid JWT token from Entra External ID (MSAL)
2. **WebSocket Client**: Python `websockets` library or browser WebSocket API
3. **Backend Running**: API server must be running and accessible

---

## Test Scenarios

### Test 1: WebSocket Connection with Valid Token

**Objective:** Verify that WebSocket accepts valid JWT token and creates authenticated SecurityContext.

**Steps:**
1. Get JWT token from browser (MSAL Local Storage)
2. Connect to WebSocket with token in query parameter: `ws://api.engram.work/api/v1/voice/voicelive/{session_id}?token={JWT}`
3. Verify connection is established
4. Check backend logs for authenticated user_id

**Expected Result:**
- WebSocket connection succeeds
- Backend logs show: `"VoiceLive WebSocket: Authenticated user {user_id} for session {session_id}"`
- SecurityContext created with `user_id = token.oid`

**Test Script:**
```bash
python3 scripts/test-voice-websocket-auth.py --token <JWT_TOKEN>
```

---

### Test 2: WebSocket Connection without Token (AUTH_REQUIRED=true)

**Objective:** Verify that WebSocket rejects connections without token when authentication is required.

**Steps:**
1. Connect to WebSocket without token: `ws://api.engram.work/api/v1/voice/voicelive/{session_id}`
2. Verify connection is rejected

**Expected Result:**
- WebSocket connection fails with status code 1008
- Reason: "Authentication required"
- Backend logs show: `"VoiceLive WebSocket: Authentication required but no token provided"`

**Test Script:**
```bash
python3 scripts/test-voice-websocket-auth.py --test-no-token
```

---

### Test 3: WebSocket Connection with Invalid Token

**Objective:** Verify that WebSocket rejects connections with invalid/expired tokens.

**Steps:**
1. Use an invalid or expired JWT token
2. Connect to WebSocket with invalid token
3. Verify connection is rejected

**Expected Result:**
- WebSocket connection fails with status code 1008
- Reason: "Invalid token"
- Backend logs show: `"VoiceLive WebSocket: Token validation failed"`

---

### Test 4: Voice Session User Attribution

**Objective:** Verify that voice sessions are created with authenticated user_id.

**Steps:**
1. Connect to WebSocket with valid token
2. Send voice messages
3. Check Zep memory for session creation
4. Verify session has correct user_id

**Expected Result:**
- Zep session created with `user_id = token.oid`
- Session metadata includes user email/display_name
- Voice transcripts attributed to authenticated user

---

## Manual Testing (Browser)

### Step 1: Get JWT Token

1. Open browser DevTools (F12)
2. Go to Application > Local Storage
3. Find key: `msal.{CLIENT_ID}.idtoken`
4. Copy token value

### Step 2: Test WebSocket Connection

```javascript
// In browser console
const token = 'YOUR_JWT_TOKEN_HERE';
const sessionId = 'test-session-' + Date.now();
const wsUrl = `wss://api.engram.work/api/v1/voice/voicelive/${sessionId}?token=${encodeURIComponent(token)}`;

const ws = new WebSocket(wsUrl);

ws.onopen = () => {
    console.log('✅ WebSocket connected');
    // Send test message
    ws.send(JSON.stringify({ type: 'agent', agent_id: 'elena' }));
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

---

## Automated Testing

### Using Test Script

```bash
# Set token
export AUTH_TOKEN='your-jwt-token-here'

# Run test
python3 scripts/test-voice-websocket-auth.py

# Test without token (should fail if AUTH_REQUIRED=true)
python3 scripts/test-voice-websocket-auth.py --test-no-token
```

### Expected Output

```
============================================================
Voice WebSocket Authentication Test
============================================================
URL: https://api.engram.work
Session ID: test-session-12345

Test 1: WebSocket connection with JWT token
------------------------------------------------------------
Connecting to WebSocket: wss://api.engram.work/api/v1/voice/voicelive/test-session-12345?token=...
✅ WebSocket connection established
✅ Test message sent
✅ Received response: ...

============================================================
Test Summary
============================================================
✅ Test 1 (with token): PASSED

✅ All tests passed!
```

---

## Backend Log Verification

Check backend logs for authentication messages:

**Success:**
```
INFO: VoiceLive WebSocket: Authenticated user d240186f-f80e-4369-9296-57fef571cd93 for session test-session-12345
```

**Failure (no token):**
```
WARNING: VoiceLive WebSocket: Authentication required but no token provided for session test-session-12345
```

**Failure (invalid token):**
```
WARNING: VoiceLive WebSocket: Token validation failed for session test-session-12345: Invalid token
```

---

## Troubleshooting

### Issue: WebSocket connection fails immediately

**Possible Causes:**
- Token expired or invalid
- Token not properly URL-encoded
- Backend not running or unreachable

**Solutions:**
- Get fresh token from browser
- Verify token is properly encoded: `encodeURIComponent(token)`
- Check backend logs for error details

### Issue: Connection succeeds but user_id is wrong

**Possible Causes:**
- Token validation not working correctly
- Fallback to POC user when AUTH_REQUIRED=false

**Solutions:**
- Verify `AUTH_REQUIRED=true` in backend settings
- Check backend logs for token validation messages
- Verify token contains correct `oid` claim

---

## Related Documentation

- `docs/architecture/user-identity-flow-comprehensive.md` - Complete user identity flow
- `docs/architecture/user-identity-fixes-required.md` - Implementation details
- `backend/api/routers/voice.py` - WebSocket handler implementation

