---
layout: default
title: "Chat Still Broken After API Parameters Fix"
parent: "Knowledge Base"
---

# Chat Still Broken After API Parameters Fix

**Date:** December 31, 2025  
**Status:** Chat endpoint still returning errors  
**Context:** Episodes, sessions, and voice are working ✅, but chat is broken ❌

---

## Current Status

- ✅ **Episodes:** Working
- ✅ **Sessions:** Working  
- ✅ **Voice:** Working
- ❌ **Chat:** Still broken

This indicates:
- **Authentication is working** (episodes/sessions/voice use same auth)
- **Issue is specific to chat endpoint** or LLM API call

---

## Recent Fix Applied

We fixed the GPT-5.1-chat API parameters:
- Changed `max_tokens` → `max_completion_tokens`
- Removed `temperature` parameter for gpt-5.1-chat models
- Code changes committed and pushed

**Fix Location:** `backend/agents/base.py` → `FoundryChatClient.ainvoke()`

---

## Possible Issues

### 1. Deployment Not Complete

**Symptom:** Code fix is deployed but deployment hasn't completed yet

**Check:**
```bash
gh run list --workflow=deploy.yml --limit 1
```

**Solution:** Wait for deployment to complete (~14 minutes)

### 2. Configuration Not Updated in Azure

**Symptom:** Code fix is correct, but Azure Container Apps environment variables are wrong

**Required Configuration:**
- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax` (base URL, no `/openai/v1/`)
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`
- `AZURE_AI_API_VERSION` = `2024-12-01-preview` ✅ (required for gpt-5.1-chat)
- `AZURE_AI_MODEL_ROUTER` = *(empty or not set)* ✅
- `AZURE_AI_KEY` = *(API key from Key Vault)*

**Check:**
```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env" \
  --output table
```

**Solution:** Update environment variables in Azure Container Apps if incorrect

### 3. Code Not Deployed

**Symptom:** Code changes committed but not yet deployed

**Check:**
- Verify code is in main branch
- Check if deployment workflow is running
- Review deployment logs

### 4. Different Error Than Expected

**Symptom:** Fix addressed one issue, but there's another problem

**Check Backend Logs:**
```bash
az containerapp logs show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --tail 200 \
  --follow
```

**Look for:**
- `"Agent execution failed: ..."`
- `"FoundryChatClient: Error calling LLM"`
- `"FoundryChatClient: Error response body: ..."`
- `"Full traceback: ..."`

### 5. Model Router Still Enabled

**Symptom:** `AZURE_AI_MODEL_ROUTER` is still set in Azure, causing wrong endpoint format

**Check:**
- Verify `AZURE_AI_MODEL_ROUTER` is empty/not set in Azure Container Apps
- Code checks: `if self.settings.azure_ai_model_router and self.settings.azure_ai_model_router.strip()`

**Solution:** Delete or clear `AZURE_AI_MODEL_ROUTER` environment variable

---

## Diagnostic Steps

### Step 1: Test Chat Endpoint

```bash
# Get JWT token from browser
python3 scripts/test-chat-debug.py \
  --token "YOUR_JWT_TOKEN" \
  --message "hi"
```

**Expected:** HTTP 200 with actual response (not error message)  
**If error:** Check response body for details

### Step 2: Check Deployment Status

```bash
gh run list --workflow=deploy.yml --limit 1 --json conclusion,status,createdAt
```

**Expected:** `conclusion: "success"`, `status: "completed"`  
**If still running:** Wait for completion

### Step 3: Verify Azure Configuration

```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env[?name=='AZURE_AI_API_VERSION' || name=='AZURE_AI_DEPLOYMENT' || name=='AZURE_AI_ENDPOINT' || name=='AZURE_AI_MODEL_ROUTER']" \
  --output table
```

**Expected:**
- `AZURE_AI_API_VERSION` = `2024-12-01-preview`
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`
- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax`
- `AZURE_AI_MODEL_ROUTER` = *(not present or empty)*

### Step 4: Check Backend Logs

```bash
az containerapp logs show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --tail 100 \
  --follow
```

**Look for chat-related errors when testing**

---

## Quick Fixes

### Fix 1: Wait for Deployment

If deployment is still running, wait for it to complete.

### Fix 2: Verify Code is Deployed

Check that the latest commit with the fix is in the deployed version:

```bash
# Check latest commit
git log --oneline -5

# Verify the fix is in the code
grep -A 10 "max_completion_tokens" backend/agents/base.py
```

### Fix 3: Update Azure Configuration

If configuration is wrong, update it:

```bash
az containerapp update \
  --name staging-env-api \
  --resource-group zimax-ai \
  --set-env-vars \
    AZURE_AI_API_VERSION=2024-12-01-preview \
    AZURE_AI_DEPLOYMENT=gpt-5.1-chat \
    AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax

# Remove Model Router if set
az containerapp update \
  --name staging-env-api \
  --resource-group zimax-ai \
  --remove-env-vars AZURE_AI_MODEL_ROUTER
```

---

## Expected Behavior After Fix

Once the fix is deployed and configuration is correct:

1. **Chat request succeeds:**
   - HTTP 200 OK
   - Response contains actual agent response (not error message)
   - `tokens_used` > 0 (indicates LLM call succeeded)

2. **Backend logs show:**
   ```
   INFO: Calling agent_chat for user ...
   INFO: FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-12-01-preview
   INFO: FoundryChatClient: Response status=200
   INFO: Agent chat succeeded: agent=elena, response_length=50
   ```

3. **Request payload includes:**
   - `max_completion_tokens` (not `max_tokens`)
   - No `temperature` parameter

---

## Related Documentation

- `docs/troubleshooting/gpt-5.1-chat-api-parameters-fix.md` - Original fix documentation
- `docs/troubleshooting/chat-error-diagnosis.md` - General chat troubleshooting
- `docs/configuration/config-alignment.md` - Configuration reference
- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router

