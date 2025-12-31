# Chat Error Diagnosis Guide

**Last Updated:** December 31, 2025

---

## Problem

Chat endpoint returns generic error: "I apologize, but I encountered an issue processing your request."

---

## Diagnostic Steps

### 1. Check Backend Logs

The improved error logging should show detailed information:

```bash
# View recent logs from Azure Container Apps
az containerapp logs show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --tail 100 \
  --follow
```

**Look for:**
- `"Agent execution failed: {error}"` - The actual error
- `"Full traceback: ..."` - Complete stack trace
- `"FoundryChatClient: Error calling LLM"` - LLM API errors
- `"FoundryChatClient: Error response body: ..."` - LLM API error details

### 2. Test Chat Endpoint Directly

Use the test script to bypass the frontend:

```bash
# Get token from browser DevTools > Application > Local Storage
# Find: msal.{clientId}.idtoken

# Test chat endpoint
python3 scripts/test-chat-quick.py \
  --token "your-jwt-token-here" \
  --message "hi"
```

This will show:
- HTTP status code
- Error response body
- Connection issues

### 3. Verify Configuration

Check Azure Container Apps environment variables:

```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env" \
  --output table
```

**Required variables:**
- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax/openai/v1/` (must include `/openai/v1/`)
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`
- `AZURE_AI_MODEL_ROUTER` = *(empty or not set)*
- `AZURE_AI_API_VERSION` = `2024-12-01-preview`
- `AZURE_AI_KEY` = *(from Key Vault)*

### 4. Common Issues

#### Issue: LLM API 400 Bad Request

**Symptoms:**
- Logs show: `"FoundryChatClient: Error response body: ..."`
- Error mentions API version or model name

**Solutions:**
1. Verify `AZURE_AI_API_VERSION` is `2024-12-01-preview`
2. Verify `AZURE_AI_DEPLOYMENT` is `gpt-5.1-chat`
3. Verify `AZURE_AI_ENDPOINT` includes `/openai/v1/`
4. Verify `AZURE_AI_MODEL_ROUTER` is empty (not set)

#### Issue: Authentication Failed

**Symptoms:**
- Logs show: `"Token validation failed"`
- HTTP 401 Unauthorized

**Solutions:**
1. Verify token is valid (not expired)
2. Check token has required scopes
3. Verify backend authentication middleware is working

#### Issue: Memory/Zep Error

**Symptoms:**
- Logs show: `"Memory enrichment failed"`
- Logs show: `"Failed to get/create session"`

**Solutions:**
1. Check Zep service is running
2. Verify `ZEP_API_URL` is correct
3. Check Zep logs for errors

#### Issue: Agent Execution Error

**Symptoms:**
- Logs show: `"Agent execution failed"`
- Full traceback shows agent graph error

**Solutions:**
1. Check agent configuration
2. Verify LangGraph dependencies
3. Check for tool execution errors

---

## Expected Log Flow (Success)

When chat works correctly, you should see:

```
INFO: Calling agent_chat for user d240186f-..., session session-xxx, agent elena
INFO: FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions
INFO: FoundryChatClient: is_openai_compat=True, model=gpt-5.1-chat
INFO: FoundryChatClient: Response status=200
INFO: Agent chat succeeded: agent=elena, response_length=50
INFO: Background task started: persisting conversation for user: d240186f-...
INFO: Background task completed: conversation persisted for user: d240186f-...
```

---

## Quick Fixes

### Fix 1: Disable Model Router

If Model Router is still enabled:

```bash
# In Azure Portal: Container Apps > Configuration > Environment variables
# Delete or set AZURE_AI_MODEL_ROUTER to empty string ""
```

### Fix 2: Update API Version

If API version is outdated:

```bash
# In Azure Portal: Container Apps > Configuration > Environment variables
# Set AZURE_AI_API_VERSION to: 2024-12-01-preview
```

### Fix 3: Fix Endpoint Format

If endpoint doesn't include `/openai/v1/`:

```bash
# In Azure Portal: Container Apps > Configuration > Environment variables
# Set AZURE_AI_ENDPOINT to: https://zimax-gw.azure-api.net/zimax/openai/v1/
```

---

## Next Steps

1. **Check logs** using the command above
2. **Test endpoint** using the test script
3. **Verify configuration** matches expected values
4. **Apply fixes** based on error messages
5. **Re-test** after fixes

---

## Related Documentation

- `docs/troubleshooting/chat-voice-errors-december-2025.md` - General troubleshooting
- `docs/configuration/config-alignment.md` - Configuration reference
- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router
- `docs/troubleshooting/api-version-model-version-mismatch.md` - API version issues

