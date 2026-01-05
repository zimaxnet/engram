---
layout: default
title: "Bypass Model Router - Use Direct Model"
parent: "Knowledge Base"
---

# Bypass Model Router - Use Direct Model

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Troubleshooting Guide

---

## Problem

The Model Router may be selecting a model (like `o4-mini`) that causes errors or requires specific API versions. You want to bypass the Model Router and use a direct model deployment (e.g., `gpt-5.1-chat` or `gpt-5-chat`) that worked before.

---

## Solution: Disable Model Router

The Model Router is enabled when `AZURE_AI_MODEL_ROUTER` is set. To bypass it and use a direct model:

### Step 1: Clear Model Router Environment Variable

**In Azure Container Apps:**
1. Go to Azure Portal > Container Apps > Your app
2. Go to **Configuration** > **Environment variables**
3. Find `AZURE_AI_MODEL_ROUTER`
4. Either:
   - **Delete** the variable, OR
   - **Set it to empty string** `""`

### Step 2: Set Direct Model Deployment

Ensure `AZURE_AI_DEPLOYMENT` is set to your direct model:

```bash
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"  # or "gpt-5-chat" if that's what worked
```

**In Azure Container Apps:**
1. Go to **Configuration** > **Environment variables**
2. Set `AZURE_AI_DEPLOYMENT` to your direct model name (e.g., `gpt-5.1-chat`)

### Step 3: Verify Configuration

After updating, the backend will:
- Use `AZURE_AI_DEPLOYMENT` directly (not Model Router)
- Log: `"Using direct deployment: {deployment}"` instead of `"Using Model Router"`
- Call the model directly without routing

---

## Configuration Comparison

### With Model Router (Current - May Cause Issues)
```bash
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax"
AZURE_AI_DEPLOYMENT="model-router"  # Not used when MODEL_ROUTER is set
AZURE_AI_MODEL_ROUTER="model-router"  # ← This enables Model Router
AZURE_AI_API_VERSION="2024-12-01-preview"
```

**Result:** Model Router selects model (may choose `o4-mini` or other models)

### Without Model Router (Direct Model - Recommended)
```bash
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax"
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"  # ← Direct model name
AZURE_AI_MODEL_ROUTER=""  # ← Empty or not set (disables Model Router)
AZURE_AI_API_VERSION="2024-10-01-preview"  # Can use older version
```

**Result:** Direct call to `gpt-5.1-chat` model

---

## Code Behavior

When `AZURE_AI_MODEL_ROUTER` is **not set or empty**:

```python
# backend/agents/base.py
deployment = self.settings.azure_ai_deployment  # Uses direct model
# Model Router check is skipped
# Calls: {endpoint}/openai/deployments/gpt-5.1-chat/chat/completions
```

When `AZURE_AI_MODEL_ROUTER` is **set**:

```python
# backend/agents/base.py
if self.settings.azure_ai_model_router:
    deployment = self.settings.azure_ai_model_router  # Uses Model Router
    # Model Router selects which model to use
    # Calls: {endpoint}/openai/deployments/model-router/chat/completions
```

---

## Quick Fix (Azure Portal)

1. **Azure Portal** > **Container Apps** > `staging-env-api`
2. **Configuration** > **Environment variables**
3. **Edit** `AZURE_AI_MODEL_ROUTER`:
   - **Option A**: Delete the variable
   - **Option B**: Set value to empty string `""`
4. **Save** (triggers new revision)
5. Wait for deployment (~14 minutes)

---

## Verification

After deployment, check backend logs for:

**With Model Router (should NOT appear):**
```
INFO: Using Model Router via APIM Gateway: model-router
```

**Without Model Router (should appear):**
```
INFO: FoundryChatClient: Calling {endpoint}/openai/deployments/gpt-5.1-chat/chat/completions
```

---

## Testing

After disabling Model Router, test chat:

```bash
python3 scripts/test-chat-quick.py --token <JWT_TOKEN> --message "hi"
```

Expected: Chat should work with direct `gpt-5.1-chat` model.

---

## Related Documentation

- `docs/sop/azure-foundry-chat-sop.md` - Model Router configuration
- `backend/agents/base.py` - Model selection logic
- `backend/core/config.py` - Configuration settings

---

## Notes

- **Model Router** is useful for automatic model selection based on workload
- **Direct Model** gives you control over which model is used
- If Model Router was selecting `o4-mini`, disabling it will use your configured `AZURE_AI_DEPLOYMENT` instead
- You can re-enable Model Router later by setting `AZURE_AI_MODEL_ROUTER` again

