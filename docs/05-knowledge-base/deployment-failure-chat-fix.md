---
layout: default
title: "Deployment Failure - Chat Fix Not Deployed"
parent: "Knowledge Base"
---

# Deployment Failure - Chat Fix Not Deployed

**Date:** January 1, 2026  
**Issue:** Chat is still broken because the deployment failed  
**Status:** Deployment failure prevented code fix from being deployed

---

## Current Status

- ✅ **Code fix committed:** GPT-5.1-chat API parameters fix is in the codebase
- ❌ **Deployment failed:** Latest deployment (2026-01-01T00:01:39Z) failed
- ❌ **Chat still broken:** Fix hasn't been deployed to Azure Container Apps
- ✅ **Episodes/Sessions/Voice:** Working (using older code without the fix)

---

## Deployment History

```
20629370015 | completed | failure | Deploy | 2026-01-01T00:01:39Z  ← Latest (FAILED)
20629361309 | completed | success | Deploy | 2026-01-01T00:01:06Z  ← Previous (SUCCESS)
20629291992 | completed | failure | Deploy | 2025-12-31T23:53:58Z  ← Earlier (FAILED)
```

---

## Next Steps

### Step 1: Check Deployment Failure Reason

```bash
gh run view 20629370015 --log-failed
```

**Common causes:**
- Build errors
- Test failures
- Azure deployment errors
- Configuration issues
- Resource constraints

### Step 2: Fix Deployment Issue

Once the deployment failure reason is identified, fix it and re-deploy.

### Step 3: Verify Deployment Succeeds

```bash
gh run list --workflow=deploy.yml --limit 1
```

Wait for deployment to complete successfully.

### Step 4: Test Chat Endpoint

After deployment succeeds:

```bash
python3 scripts/test-chat-debug.py \
  --token "YOUR_JWT_TOKEN" \
  --message "hi"
```

**Expected:** HTTP 200 with actual agent response (not error message)

---

## Important Note: Endpoint Format Configuration

**There's a configuration discrepancy:**

The documentation says:
- `AZURE_AI_ENDPOINT` should include `/openai/v1/` for OpenAI-compatible format

But the actual endpoint you're using is:
- `https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions`

This is the **Azure Foundry format** (not OpenAI-compatible format).

**The code handles both formats:**
- ✅ If endpoint contains `/openai/v1` → Uses OpenAI-compatible format (model in body)
- ✅ Otherwise → Uses Azure Foundry format (deployment in path) ← **This is what you're using**

**For Azure Foundry format (your case):**
- Endpoint should be: `https://zimax-gw.azure-api.net/zimax` (base URL)
- Code constructs: `{base}/openai/deployments/{deployment}/chat/completions?api-version={api_version}`
- Our fix applies: `max_completion_tokens` and no `temperature` for gpt-5.1-chat

---

## Configuration for Azure Foundry Format

Based on your actual endpoint usage:

```bash
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax"  # Base URL (no /openai/v1/)
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"
AZURE_AI_API_VERSION="2024-12-01-preview"
AZURE_AI_MODEL_ROUTER=""  # Empty = use direct model
AZURE_AI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
```

**Code will construct:**
```
https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-12-01-preview
```

**Payload will include:**
- `max_completion_tokens` (not `max_tokens`) ✅ Fixed
- No `temperature` parameter ✅ Fixed

---

## Summary

1. **Code fix is correct** - Handles Azure Foundry format with gpt-5.1-chat parameters
2. **Deployment failed** - Fix hasn't been deployed yet
3. **Need to fix deployment** - Check failure logs and resolve
4. **Then re-deploy** - Once fixed, deployment will include the chat fix
5. **Chat should work** - After successful deployment with the fix

---

## Related Documentation

- `docs/troubleshooting/gpt-5.1-chat-api-parameters-fix.md` - The code fix
- `docs/troubleshooting/chat-still-broken-after-parameter-fix.md` - Troubleshooting guide
- `backend/agents/base.py` - Code implementation

