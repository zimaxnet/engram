# Chat Test Results with Real JWT Token

**Date:** December 31, 2025  
**Test Method:** Command-line with authenticated JWT token  
**Status:** ❌ Agent execution failing (authentication ✅ working)

---

## Test Results

### Request
- **URL:** `https://api.engram.work/api/v1/chat`
- **Method:** POST
- **Authentication:** ✅ Valid JWT token (Bearer token)
- **Payload:**
  ```json
  {
    "content": "hi",
    "agent_id": "elena"
  }
  ```

### Response
- **Status:** `200 OK` ✅
- **Response Time:** ~1522ms
- **Authentication:** ✅ **WORKING** (token accepted)
- **Agent Execution:** ❌ **FAILING** (error message returned)
- **LLM Call:** ❌ **FAILING** (`tokens_used: 0`)

### Response Body
```json
{
  "message_id": "584d1391-e92a-426b-87b7-1b393de0cf0d",
  "content": "I apologize, but I encountered an issue processing your request. Could you please try again? If the problem persists, the team can check the logs for more details.",
  "agent_id": "elena",
  "agent_name": "Dr. Elena Vasquez",
  "timestamp": "2025-12-31T23:28:11.957420Z",
  "tokens_used": 0,
  "latency_ms": 1521.46315574646,
  "session_id": "5d8965ce-712b-4b0d-9e5e-4e51809d3cf7"
}
```

---

## Key Findings

### ✅ What's Working
1. **API Endpoint:** Responding correctly (200 OK)
2. **Authentication:** ✅ **JWT token validation is working correctly**
3. **Request Routing:** Request reaches chat handler
4. **Error Handling:** Exception is caught and handled gracefully

### ❌ What's Failing
1. **Agent Execution:** The `agent_chat()` function is throwing an exception
2. **LLM API Call:** No tokens consumed (`tokens_used: 0`) = LLM call failed
3. **Response Generation:** Falling back to generic error message

---

## Root Cause

The `tokens_used: 0` is the definitive indicator that the LLM API call is failing. The authentication is working, so the issue is **NOT** with user authentication.

### Most Likely Causes

#### 1. LLM API Configuration Issue (Most Likely)
The Azure AI Foundry API call is failing. Possible causes:

- **Endpoint format:** `AZURE_AI_ENDPOINT` missing `/openai/v1/`
- **API version:** `AZURE_AI_API_VERSION` not `2024-12-01-preview`
- **Model Router:** `AZURE_AI_MODEL_ROUTER` still enabled (should be empty)
- **Deployment name:** `AZURE_AI_DEPLOYMENT` not `gpt-5.1-chat`
- **API key:** `AZURE_AI_KEY` missing or invalid

#### 2. LLM API 400 Bad Request
Azure AI Foundry is returning a 400 error, likely due to:
- API version mismatch
- Model name mismatch
- Endpoint format issue
- Invalid request payload

#### 3. Network/Connectivity Issue
The backend cannot reach the Azure AI Foundry endpoint (less likely, as this would show connection timeout).

---

## Next Steps: Check Backend Logs

The improved logging should show the exact error. **Check Azure Container Apps logs:**

```bash
# View recent logs
az containerapp logs show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --tail 200 \
  --follow
```

### What to Look For

The logs should contain these messages (from the improved logging):

1. **Agent execution start:**
   ```
   INFO: Calling agent_chat for user d240186f-..., session ..., agent elena
   ```

2. **LLM API call attempt:**
   ```
   INFO: FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions
   INFO: FoundryChatClient: is_openai_compat=True, model=gpt-5.1-chat
   ```

3. **Error messages:**
   ```
   ERROR: Agent execution failed: {error}
   ERROR: FoundryChatClient: Error calling LLM: {error}
   ERROR: FoundryChatClient: Error response body: {error_body}
   ERROR: Full traceback: {traceback}
   ```

### Expected Error Patterns

**If LLM API returns 400:**
```
ERROR: FoundryChatClient: Response status=400
ERROR: FoundryChatClient: Error response body: {"error": {"message": "Model o4-mini is enabled only for api versions 2024-12-01-preview and later"}}
```

**If endpoint format is wrong:**
```
ERROR: FoundryChatClient: Error calling LLM: 404 Not Found
ERROR: FoundryChatClient: Request URL: https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions
```

**If API key is missing:**
```
ERROR: FoundryChatClient: Error calling LLM: 401 Unauthorized
```

---

## Verify Azure Configuration

Check environment variables in Azure Container Apps:

```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env" \
  --output table
```

**Required values:**
- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax/openai/v1/` ✅ (must include `/openai/v1/`)
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat` ✅
- `AZURE_AI_API_VERSION` = `2024-12-01-preview` ✅
- `AZURE_AI_MODEL_ROUTER` = *(empty or not set)* ✅
- `AZURE_AI_KEY` = *(from Key Vault)* ✅

---

## Test Command

To reproduce this test:

```bash
python3 scripts/test-chat-debug.py \
  --token "YOUR_JWT_TOKEN_HERE" \
  --message "hi"
```

---

## Related Documentation

- `docs/troubleshooting/chat-backend-test-results.md` - Previous test results
- `docs/troubleshooting/chat-error-diagnosis.md` - Diagnostic guide
- `docs/configuration/config-alignment.md` - Configuration reference
- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router
- `docs/troubleshooting/api-version-model-version-mismatch.md` - API version issues

