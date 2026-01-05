---
layout: default
title: "Azure AI Foundry 400 Bad Request - Investigation"
parent: "Knowledge Base"
---

# Azure AI Foundry 400 Bad Request - Investigation

## Status: 🔍 INVESTIGATING

**Date**: 2025-12-31  
**Issue**: Azure AI Foundry API returns 400 Bad Request when calling model-router endpoint

## Current Error

```
FoundryChatClient: Error calling LLM: Client error '400 Bad Request' 
for url 'https://zimax-gw.azure-api.net/zimax/openai/deployments/model-router/chat/completions?api-version=2024-10-01-preview'
```

## Endpoint Details

- **URL**: `https://zimax-gw.azure-api.net/zimax/openai/deployments/model-router/chat/completions?api-version=2024-10-01-preview`
- **Type**: APIM Gateway (not direct Azure AI Foundry)
- **Format**: Azure AI Foundry format (`/openai/deployments/{deployment}/chat/completions`)
- **API Version**: `2024-10-01-preview`
- **Deployment**: `model-router`

## Code Configuration

From `backend/agents/base.py`:

```python
# Endpoint detection
is_azure_openai = "openai.azure.com" in endpoint
is_apim_gateway = "/openai/v1" in endpoint  # This is FALSE for this endpoint

# URL construction
if not is_azure_openai and not is_apim_gateway:
    # Azure AI Foundry format
    self.url = f"{base}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    self.is_openai_compat = False
    self.model = None

# Payload construction
payload = {
    "messages": [self._format_message(m) for m in messages],
}
# NO model parameter (is_openai_compat=False)
# Adds temperature and max_tokens (is_openai_compat=False)
if not self.is_openai_compat:
    payload["temperature"] = self.temperature
    payload["max_tokens"] = self.max_tokens
```

## Possible Issues

### 1. APIM Gateway Expects OpenAI-Compatible Format

**Hypothesis**: APIM Gateway might expect OpenAI-compatible format even though URL suggests Foundry format.

**Test**: Try setting `is_openai_compat=True` for APIM Gateway endpoints.

### 2. Missing Required Fields

**Hypothesis**: APIM Gateway might require additional fields in the request.

**Possible Missing Fields**:
- `model` parameter (even for Foundry format)
- Different API version
- Additional headers

### 3. Model Router Configuration

**Hypothesis**: The `model-router` deployment might not be configured correctly in APIM Gateway.

**Check**: Verify model-router deployment exists and is accessible.

### 4. Authentication Issues

**Hypothesis**: Bearer token or API key might be invalid or missing required scopes.

**Check**: Verify authentication headers are correct.

## Enhanced Error Logging

We've added enhanced error logging to capture:
- Error response body from API
- Request URL
- Payload structure
- Message count

**Next Step**: After deployment completes, trigger a chat request and check logs for:
```
FoundryChatClient: Error response body: {actual error message}
FoundryChatClient: Request payload keys: [...]
FoundryChatClient: Payload messages count: X
```

## Investigation Steps

1. ✅ **Enhanced Error Logging** - Added to capture error response body
2. ⏳ **Wait for Deployment** - Latest code with enhanced logging
3. ⏳ **Trigger Chat Request** - Get actual error message from API
4. ⏳ **Analyze Error Response** - Determine exact issue
5. ⏳ **Fix Request Format** - Update payload/headers based on error
6. ⏳ **Test Again** - Verify fix works

## Related Files

- `backend/agents/base.py` - FoundryChatClient implementation
- `backend/core/config.py` - Azure AI configuration
- `docs/troubleshooting/chat-endpoint-errors.md` - Related errors

---

**Status**: Waiting for enhanced error logging to capture actual error message from Azure AI Foundry API

