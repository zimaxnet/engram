---
layout: default
title: "GPT-5.1-chat API Parameters Fix"
parent: "Knowledge Base"
---

# GPT-5.1-chat API Parameters Fix

**Date:** December 31, 2025  
**Issue:** Chat endpoint failing with LLM API errors  
**Root Cause:** `gpt-5.1-chat` model has different API parameter requirements

---

## Problem

Chat endpoint was returning error messages because the LLM API calls were failing with:
- `400 Bad Request: Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.`
- `400 Bad Request: Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported.`

---

## Root Cause

The `gpt-5.1-chat` model (version `2025-11-13`) has different API parameter requirements than older models:

1. **`max_tokens` → `max_completion_tokens`**: The model requires `max_completion_tokens` instead of `max_tokens`
2. **Temperature not supported**: The model only supports the default temperature value (1), custom values like 0.7 are not allowed
3. **API version**: Requires `2024-12-01-preview` or later (not `2024-05-01-preview`)

---

## Solution

Updated `backend/agents/base.py` `FoundryChatClient` class to:

1. **Use `max_completion_tokens` for Azure format endpoints** (instead of `max_tokens`)
2. **Skip `temperature` parameter for `gpt-5.1-chat` models** (only send for older models)
3. **Store deployment name** to enable model-specific handling

### Code Changes

```python
# Store deployment name for model-specific handling
self.deployment = deployment

# In ainvoke method:
if not self.is_openai_compat:
    # gpt-5.1-chat doesn't support custom temperature, so don't send it
    # For older models, temperature is supported
    if self.deployment and "gpt-5.1" not in self.deployment.lower():
        payload["temperature"] = self.temperature
    # Use max_completion_tokens for newer models (gpt-5.1-chat, etc.)
    payload["max_completion_tokens"] = self.max_tokens
```

---

## Testing

### Before Fix

```bash
# Test with max_tokens and temperature
curl -X POST \
  -H "api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Say hi"}],
    "temperature": 0.7,
    "max_tokens": 100
  }' \
  "https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-12-01-preview"

# Result: 400 Bad Request
```

### After Fix

```bash
# Test with max_completion_tokens and no temperature
curl -X POST \
  -H "api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Say hi"}],
    "max_completion_tokens": 100
  }' \
  "https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-12-01-preview"

# Result: 200 OK ✅
```

---

## Configuration Requirements

Ensure these environment variables are set correctly:

- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax` (base URL, no `/openai/v1/`)
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`
- `AZURE_AI_API_VERSION` = `2024-12-01-preview` (required for gpt-5.1-chat)
- `AZURE_AI_MODEL_ROUTER` = *(empty or not set)*
- `AZURE_AI_KEY` = *(API key from Key Vault)*

---

## Model Compatibility

| Model | max_tokens | max_completion_tokens | temperature | API Version |
|-------|-----------|---------------------|-------------|-------------|
| `gpt-4`, `gpt-35-turbo` | ✅ | ❌ | ✅ (custom) | `2024-05-01-preview` |
| `gpt-5.1-chat` | ❌ | ✅ | ❌ (default only) | `2024-12-01-preview` |

---

## Related Documentation

- `docs/troubleshooting/api-version-model-version-mismatch.md` - API version issues
- `docs/troubleshooting/chat-error-diagnosis.md` - General chat troubleshooting
- `docs/configuration/config-alignment.md` - Configuration reference

