---
layout: default
title: "Chat Deployment Issues Summary"
parent: "Knowledge Base"
---

# Chat Deployment Issues Summary

**Date:** January 1, 2026  
**Status:** Chat broken due to deployment failure

---

## Root Cause

The latest deployment failed because:
1. **Deployment conflict:** Previous deployment was still active (deployments triggered 33 seconds apart)
2. **Model Router still configured:** Deployment parameters show `azureAiModelRouter=model-router` is still set

---

## Deployment Failure Details

**Error:**
```
DeploymentActive: cannot be saved, because this would overwrite an existing deployment 
which is still active. The previous deployment was started at '1/1/2026 12:01:56 AM'
```

**Deployment History:**
- 00:01:06Z - Previous deployment (SUCCESS)
- 00:01:39Z - Latest deployment (FAILED - active deployment conflict)

**Time between deployments:** 33 seconds (violates 14-minute rule)

---

## Configuration Issue

**Model Router is still enabled:**
```
azureAiModelRouter=model-router
```

This should be empty or not set to use direct model deployment.

---

## Current Status

- ✅ **Code fix committed:** GPT-5.1-chat API parameters fix is in codebase
- ❌ **Deployment failed:** Active deployment conflict
- ❌ **Chat still broken:** Fix not deployed
- ⚠️ **Model Router enabled:** Should be disabled
- ✅ **Episodes/Sessions/Voice:** Working (using older code)

---

## Solution Steps

### Step 1: Wait or Cancel Active Deployment

The active deployment will expire on `1/8/2026 12:01:56 AM` if it doesn't complete.

**Option A: Wait**
- Wait for the active deployment to complete or fail
- Then re-trigger deployment

**Option B: Cancel (if possible)**
- Check Azure Portal for active deployments
- Cancel if stuck

### Step 2: Disable Model Router in Deployment

The deployment parameters need to be updated to remove Model Router:

**Current (WRONG):**
```
azureAiModelRouter=model-router
```

**Should be:**
```
azureAiModelRouter=  (empty)
```

This needs to be fixed in:
- GitHub Actions workflow parameters
- Bicep template parameters (if applicable)

### Step 3: Wait for Deployment Window

**IMPORTANT:** Follow the 14-minute rule:
- Wait at least 14 minutes between deployments
- Check deployment status before triggering new one

### Step 4: Re-trigger Deployment

Once the active deployment completes/fails and Model Router is disabled:

1. Ensure code is committed
2. Wait for deployment window (14 minutes)
3. Trigger deployment (or push to trigger)
4. Monitor deployment status
5. Wait for completion

### Step 5: Verify Configuration

After deployment succeeds, verify Azure Container Apps configuration:

```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env[?name=='AZURE_AI_MODEL_ROUTER' || name=='AZURE_AI_API_VERSION' || name=='AZURE_AI_DEPLOYMENT']" \
  --output table
```

**Expected:**
- `AZURE_AI_MODEL_ROUTER` = *(not present or empty)*
- `AZURE_AI_API_VERSION` = `2024-12-01-preview`
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`

### Step 6: Test Chat

After successful deployment:

```bash
python3 scripts/test-chat-debug.py \
  --token "YOUR_JWT_TOKEN" \
  --message "hi"
```

**Expected:** HTTP 200 with actual agent response

---

## Files to Update

### 1. GitHub Actions Workflow

Check `.github/workflows/deploy.yml` for:
```yaml
azureAiModelRouter: model-router  # ❌ Should be empty
```

Change to:
```yaml
azureAiModelRouter: ""  # ✅ Empty = use direct model
```

Or remove the parameter entirely if it's optional.

### 2. Bicep Template (if applicable)

Check `infra/main.bicep` for Model Router parameter default.

---

## Summary

1. **Deployment conflict** - Wait for active deployment to complete
2. **Model Router enabled** - Disable in deployment parameters
3. **Code fix ready** - Already committed, just needs successful deployment
4. **Follow 14-minute rule** - Don't trigger deployments too quickly
5. **Verify after deploy** - Check configuration and test chat endpoint

Once these issues are resolved and deployment succeeds, chat should work.

---

## Related Documentation

- `docs/troubleshooting/deployment-failure-chat-fix.md` - Deployment failure details
- `docs/troubleshooting/gpt-5.1-chat-api-parameters-fix.md` - Code fix details
- `.github/workflows/deploy.yml` - Deployment workflow

