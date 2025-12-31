# API Version and Model Version Mismatch

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Troubleshooting Guide

---

## Problem

The Target URI shows an outdated API version (`2024-05-01-preview`) that may not support the model version (`2025-11-13`).

**Example Error:**
```
Target URI: https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-05-01-preview
Model Version: 2025-11-13
```

---

## Root Cause

1. **Outdated API Version**: `2024-05-01-preview` is too old for model version `2025-11-13`
2. **Wrong URL Format**: Using Azure OpenAI format (`/openai/deployments/...`) instead of OpenAI SDK format (`/openai/v1/chat/completions`)

---

## Solution

### Step 1: Update API Version

**In Azure Container Apps:**
1. Go to **Configuration** → **Environment variables**
2. Find `AZURE_AI_API_VERSION`
3. Set to: `2024-12-01-preview`
4. **Save** (triggers new revision)

### Step 2: Verify Endpoint Format

Ensure `AZURE_AI_ENDPOINT` includes `/openai/v1/`:

```bash
# ✅ Correct
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"

# ❌ Wrong (will use Azure OpenAI format)
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax"
```

### Step 3: Verify Configuration

After deployment, check logs for:

**Should see (OpenAI SDK format):**
```
INFO: FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions
INFO: FoundryChatClient: is_openai_compat=True, model=gpt-5.1-chat
```

**Should NOT see (Azure OpenAI format):**
```
INFO: FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-05-01-preview
```

---

## Model Version Compatibility

| Model Version | Minimum API Version | Recommended API Version |
|--------------|---------------------|-------------------------|
| `2025-11-13` | `2024-12-01-preview` | `2024-12-01-preview` |
| `2025-08-28` | `2024-10-01-preview` | `2024-12-01-preview` |
| Older versions | `2024-05-01-preview` | `2024-10-01-preview` |

---

## Configuration Summary

**Correct Configuration:**
```bash
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"
AZURE_AI_API_VERSION="2024-12-01-preview"  # ← Updated for model version 2025-11-13
AZURE_AI_MODEL_ROUTER=""  # Empty = use direct model
```

---

## Verification

After updating, test the endpoint:

```bash
python3 scripts/test-chat-quick.py --token <JWT_TOKEN> --message "hi"
```

Expected: Chat should work with the updated API version.

---

## Related Documentation

- `docs/configuration/config-alignment.md` - Complete configuration guide
- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router
- `backend/agents/base.py` - FoundryChatClient implementation

