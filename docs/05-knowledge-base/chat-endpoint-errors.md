---
layout: default
title: "Chat Endpoint Errors - Analysis"
parent: "Knowledge Base"
---

# Chat Endpoint Errors - Analysis

## Status: 🔍 INVESTIGATING

**Date**: 2025-12-31  
**Issue**: Chat endpoint returns error message after authentication/CORS fixes

## Symptoms

User reports:
- ✅ Authentication working (no 401 errors)
- ✅ CORS working (OPTIONS requests succeed)
- ❌ Chat endpoint returns: "I apologize, but I encountered an issue processing your request..."

## Root Causes Identified

### 1. Zep Memory Service - User Not Found

**Error**:
```
Zep API error: 400 - POST https://zep.engram.work/api/v1/sessions 
bad request: user does not exist with user_id: poc-user
```

**Analysis**:
- When `AUTH_REQUIRED=false`, the backend returns `user_id="poc-user"` (from `auth.py:500`)
- Zep memory service requires users to exist before creating sessions
- The code has retry logic (lines 137-146 in `memory/client.py`) to create sessions without `user_id` if user doesn't exist
- However, the error still occurs, suggesting the retry might not be working correctly

**Impact**: Non-blocking - the code falls back to offline mode, but memory features won't work

### 2. Azure AI Foundry API - 400 Bad Request

**Error**:
```
FoundryChatClient: Error calling LLM: Client error '400 Bad Request' 
for url 'https://zimax-gw.azure-api.net/zimax/openai/deployments/model-router/chat/completions?api-version=2024-10-01-preview'
```

**Analysis**:
- The endpoint is an **APIM Gateway** (`zimax-gw.azure-api.net`), not direct Azure AI Foundry
- The URL format suggests it's using Azure AI Foundry format (`/openai/deployments/{deployment}/chat/completions`)
- The code sets `is_openai_compat=False` for this endpoint
- When `is_openai_compat=False`, the code adds `temperature` and `max_tokens` to payload
- The 400 error suggests the request format might be incorrect for APIM Gateway

**Possible Issues**:
1. **APIM Gateway expects different format**: APIM might expect OpenAI-compatible format even though URL suggests Foundry format
2. **Model Router deployment**: The `model-router` deployment might not exist or be misconfigured
3. **API Version**: The `api-version=2024-10-01-preview` might not be supported
4. **Missing required fields**: The payload might be missing fields required by APIM Gateway
5. **Authentication**: The bearer token or API key might be invalid

**Impact**: **BLOCKING** - Chat responses cannot be generated

## Code Flow

1. User sends message → `/api/v1/chat` (POST)
2. Authentication middleware → Returns `poc-user` (AUTH_REQUIRED=false)
3. Chat router → Gets/creates session with `poc-user`
4. Zep memory → Fails to create session (user doesn't exist), retries without user_id
5. Agent execution → Calls Azure AI Foundry via APIM Gateway
6. **Azure AI Foundry → Returns 400 Bad Request** ❌
7. Error handler → Returns generic error message to user

## Next Steps

### Immediate Actions

1. **Add Enhanced Error Logging** (✅ Done - pending deployment)
   - Log error response body from Azure AI Foundry
   - Log request payload structure
   - This will reveal the actual error message from the API

2. **Verify APIM Gateway Configuration**
   - Check if `model-router` deployment exists
   - Verify API version is correct
   - Check if APIM Gateway expects OpenAI-compatible format

3. **Test Request Format**
   - Try with `is_openai_compat=True` to see if APIM expects OpenAI format
   - Check if payload needs additional fields

### Investigation Steps

1. **Wait for deployment** with enhanced error logging
2. **Trigger chat request** and check logs for detailed error response
3. **Analyze error response** to determine exact issue
4. **Fix request format** based on error message
5. **Test again** to verify fix

## Related Files

- `backend/agents/base.py` - FoundryChatClient implementation
- `backend/memory/client.py` - Zep memory client (user handling)
- `backend/api/middleware/auth.py` - Authentication (returns poc-user)
- `backend/api/routers/chat.py` - Chat endpoint (error handling)

## Environment Variables

- `AUTH_REQUIRED=false` - Causes `poc-user` to be used
- `AZURE_AI_ENDPOINT` - Should point to APIM Gateway
- `AZURE_AI_MODEL_ROUTER` - Should be `model-router`
- `AZURE_AI_API_VERSION` - Should be `2024-10-01-preview`

---

**Status**: Waiting for enhanced error logging deployment to get detailed error message

