---
layout: default
title: "Chat and Voice Errors - December 2025"
parent: "Knowledge Base"
---

# Chat and Voice Errors - December 2025

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Troubleshooting Guide

---

## Reported Issues

### Issue 1: Chat Returns Generic Error Message

**Symptom:**
- User sends message: "hi"
- Response: "I apologize, but I encountered an issue processing your request. Could you please try again? If the problem persists, the team can check the logs for more details."

**Root Cause Analysis:**
The chat endpoint catches exceptions in the `agent_chat` execution and returns a generic error message. The actual error is logged but not visible to the user.

**Possible Causes:**
1. **LLM API Error**: Azure AI Foundry API returning 400/500 error
2. **Tool Execution Error**: Agent tool invocation failing (possibly related to user_id injection)
3. **Memory Enrichment Error**: Zep memory operations failing
4. **Context Initialization Error**: EnterpriseContext creation failing

**Debugging Steps:**

1. **Check Backend Logs:**
   ```bash
   # Look for these log messages:
   - "Agent execution failed: {error}"
   - "Error details: {error_details}"
   - "Full traceback: {traceback}"
   ```

2. **Check LLM API Calls:**
   ```bash
   # Look for FoundryChatClient errors:
   - "FoundryChatClient: Error calling LLM: {error}"
   - "FoundryChatClient: Error response body: {body}"
   ```

3. **Check Tool Execution:**
   ```bash
   # Look for tool-related errors:
   - "Tool execution error for {tool_name}: {error}"
   - "Could not inspect schema for tool {tool_name}: {error}"
   ```

4. **Test Chat Endpoint Directly:**
   ```bash
   python3 scripts/test-chat-quick.py --token <JWT_TOKEN> --message "hi"
   ```

**Recent Changes That Might Affect This:**
- Tool schema inspection for user_id injection (added in user identity fixes)
- Background task logging (should not affect chat execution)
- MCP tool signatures (should not affect direct chat)

**Fix Applied:**
- Added full traceback logging to capture actual error
- Improved error handling in tool schema inspection
- Better fallback agent retrieval

---

### Issue 2: Voice Button Clicks But No Response

**Symptom:**
- User clicks voice button
- Button appears to work (no immediate error)
- No audio response or connection feedback

**Root Cause Analysis:**
Voice WebSocket connection may be failing silently or closing immediately.

**Possible Causes:**
1. **Authentication Failure**: Token not available or invalid
2. **WebSocket Connection Failure**: Backend rejecting connection
3. **Token Acquisition Failure**: `getAccessToken()` returning null
4. **WebSocket Close Immediately**: Backend closing connection with code 1008

**Debugging Steps:**

1. **Check Browser Console:**
   ```javascript
   // Look for these messages:
   - "Voice WebSocket connected successfully"
   - "Voice WebSocket closed" (with code and reason)
   - "Voice WebSocket authentication failed"
   - "No access token available for voice WebSocket"
   ```

2. **Check WebSocket URL:**
   ```javascript
   // In browser console, check the WebSocket URL:
   console.log('WebSocket URL:', wsUrl);
   // Should include: ?token=...
   ```

3. **Check Token Availability:**
   ```javascript
   // In browser console:
   import { getAccessToken } from './auth/authConfig';
   const token = await getAccessToken();
   console.log('Token available:', !!token);
   ```

4. **Check Backend Logs:**
   ```bash
   # Look for these messages:
   - "VoiceLive WebSocket: Authenticated user {user_id}"
   - "VoiceLive WebSocket: Authentication required but no token provided"
   - "VoiceLive WebSocket: Token validation failed"
   ```

**Recent Changes That Might Affect This:**
- WebSocket authentication with token in query parameter (just added)
- Token extraction from `getAccessToken()` (may return null if not logged in)

**Fix Applied:**
- Added try/catch for token acquisition
- Improved error messages with specific close codes
- Added console logging for debugging
- Better handling when token is not available

---

## Quick Diagnostic Commands

### Check Chat Endpoint
```bash
# Test chat with token
python3 scripts/test-chat-quick.py --token <JWT_TOKEN> --message "hi"

# Check for errors in response
curl -X POST https://api.engram.work/api/v1/chat \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "hi", "agent_id": "elena", "session_id": "test"}'
```

### Check Voice WebSocket
```bash
# Test WebSocket connection
python3 scripts/test-voice-websocket-auth.py --token <JWT_TOKEN>

# Check browser console for WebSocket errors
# Open DevTools > Console > Look for "Voice WebSocket" messages
```

### Check Backend Logs
```bash
# Look for recent errors
# Check Azure Container Apps logs or local logs for:
# - "Agent execution failed"
# - "VoiceLive WebSocket"
# - "FoundryChatClient: Error"
```

---

## Common Error Patterns

### Pattern 1: LLM API 400 Error
**Symptoms:**
- Chat fails with generic error
- Backend logs show: "FoundryChatClient: Error response body: ..."

**Possible Causes:**
- API version mismatch
- Model not available
- Invalid request format

**Solution:**
- Check `AZURE_AI_API_VERSION` environment variable
- Verify model is available in Azure AI Foundry
- Check request payload format

### Pattern 2: Authentication Token Issues
**Symptoms:**
- Voice WebSocket closes immediately
- Code 1008: "Authentication required" or "Invalid token"

**Possible Causes:**
- Token expired
- Token not in query parameter
- Token validation failing

**Solution:**
- Get fresh token from browser
- Verify token is in WebSocket URL query parameter
- Check backend token validation logs

### Pattern 3: Tool Execution Errors
**Symptoms:**
- Chat fails when agent tries to use tools
- Backend logs show tool-related errors

**Possible Causes:**
- Tool schema inspection failing
- user_id injection causing issues
- Tool not accepting parameters

**Solution:**
- Check tool schema inspection code
- Verify user_id is being injected correctly
- Check tool implementation

---

## Next Steps

1. **Check Backend Logs**: Review Azure Container Apps logs for actual error messages
2. **Test Endpoints**: Use test scripts to isolate the issue
3. **Check Browser Console**: Look for frontend errors and WebSocket messages
4. **Verify Authentication**: Ensure tokens are valid and being passed correctly

---

## Related Documentation

- `docs/troubleshooting/azure-ai-foundry-400-investigation.md` - LLM API errors
- `docs/architecture/user-identity-flow-comprehensive.md` - User identity flow
- `scripts/test-chat-quick.py` - Chat testing script
- `scripts/test-voice-websocket-auth.py` - Voice WebSocket testing script

