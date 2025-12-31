# Chat Backend Test Results

**Date:** December 31, 2025  
**Test Method:** Command-line direct API call  
**Status:** ❌ Agent execution failing

---

## Test Results

### Request
- **URL:** `https://api.engram.work/api/v1/chat`
- **Method:** POST
- **Authentication:** None (AUTH_REQUIRED may be false or token not required)
- **Payload:**
  ```json
  {
    "content": "hi",
    "agent_id": "elena"
  }
  ```

### Response
- **Status:** `200 OK` ✅
- **Response Time:** ~925ms
- **Content:** Error message (generic fallback)
- **Tokens Used:** `0` ❌ (indicates LLM call failed)

### Response Body
```json
{
  "message_id": "55facc42-eb32-4874-807d-e8167e279b5b",
  "content": "I apologize, but I encountered an issue processing your request. Could you please try again? If the problem persists, the team can check the logs for more details.",
  "agent_id": "elena",
  "agent_name": "Dr. Elena Vasquez",
  "timestamp": "2025-12-31T22:38:05.733070Z",
  "tokens_used": 0,
  "latency_ms": 924.6950149536133,
  "session_id": "b4847e8c-2fb9-47d4-8cc7-867588041318"
}
```

---

## Diagnosis

### ✅ What's Working
1. **API Endpoint:** Responding correctly (200 OK)
2. **Authentication:** Request accepted (either AUTH_REQUIRED=false or token validation passed)
3. **Request Routing:** Request reaches the chat handler
4. **Error Handling:** Error is caught and generic message returned

### ❌ What's Failing
1. **Agent Execution:** The `agent_chat()` call is failing
2. **LLM API Call:** No tokens used = LLM call didn't succeed
3. **Response Generation:** Falling back to error message

---

## Root Cause Analysis

The `tokens_used: 0` is the key indicator. This means:

1. **Agent execution started** (request reached handler)
2. **Agent execution failed** (caught by exception handler)
3. **LLM call never succeeded** (no tokens consumed)

### Most Likely Causes

#### 1. LLM API Configuration Issue (Most Likely)
- **Symptom:** `tokens_used: 0`, fast failure (~1 second)
- **Possible causes:**
  - `AZURE_AI_ENDPOINT` missing `/openai/v1/`
  - `AZURE_AI_API_VERSION` incorrect (needs `2024-12-01-preview`)
  - `AZURE_AI_MODEL_ROUTER` still enabled (should be empty)
  - `AZURE_AI_DEPLOYMENT` incorrect (should be `gpt-5.1-chat`)
  - `AZURE_AI_KEY` missing or invalid

#### 2. LLM API 400 Bad Request
- **Symptom:** Fast failure, no tokens
- **Error in logs:** `FoundryChatClient: Error response body: ...`
- **Common causes:**
  - API version mismatch
  - Model name mismatch
  - Endpoint format incorrect

#### 3. Agent Graph Execution Error
- **Symptom:** Exception during agent graph execution
- **Error in logs:** `Agent execution failed: ...`
- **Possible causes:**
  - Tool execution error
  - Memory enrichment error
  - LangGraph state error

---

## Next Steps

### 1. Check Backend Logs

The improved logging should show:

```bash
# View Azure Container Apps logs
az containerapp logs show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --tail 200 \
  --follow
```

**Look for:**
- `"Calling agent_chat for user ..."`
- `"Agent execution failed: ..."`
- `"FoundryChatClient: Error calling LLM"`
- `"FoundryChatClient: Error response body: ..."`
- `"Full traceback: ..."`

### 2. Verify Azure Configuration

Check environment variables in Azure Container Apps:

```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env" \
  --output table
```

**Required values:**
- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax/openai/v1/`
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`
- `AZURE_AI_API_VERSION` = `2024-12-01-preview`
- `AZURE_AI_MODEL_ROUTER` = *(empty or not set)*
- `AZURE_AI_KEY` = *(from Key Vault)*

### 3. Test with Authentication Token

Test with a real JWT token to ensure authenticated user context:

```bash
# Get token from browser DevTools > Application > Local Storage
# Find: msal.{clientId}.idtoken

python3 scripts/test-chat-debug.py \
  --token "your-jwt-token-here" \
  --message "hi"
```

### 4. Test LLM API Directly

Verify the LLM API configuration works:

```python
from openai import OpenAI

endpoint = "https://zimax-gw.azure-api.net/zimax/openai/v1/"
deployment_name = "gpt-5.1-chat"
api_key = "your-api-key"

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[{"role": "user", "content": "hi"}],
    temperature=0.7,
)

print(completion.choices[0].message)
```

---

## Expected Log Flow (When Fixed)

When chat works correctly, logs should show:

```
INFO: Calling agent_chat for user ..., session ..., agent elena
INFO: FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions
INFO: FoundryChatClient: is_openai_compat=True, model=gpt-5.1-chat
INFO: FoundryChatClient: Response status=200
INFO: Agent chat succeeded: agent=elena, response_length=50
INFO: Background task started: persisting conversation for user: ...
INFO: Background task completed: conversation persisted for user: ...
```

---

## Test Scripts

- `scripts/test-chat-debug.py` - Enhanced debugging test
- `scripts/test-chat-quick.py` - Quick test script
- `docs/troubleshooting/chat-error-diagnosis.md` - Full diagnostic guide

---

## Related Documentation

- `docs/troubleshooting/chat-error-diagnosis.md` - Diagnostic steps
- `docs/configuration/config-alignment.md` - Configuration reference
- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router
- `docs/troubleshooting/api-version-model-version-mismatch.md` - API version issues

