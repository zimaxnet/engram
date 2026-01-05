---
layout: default
title: "Deployment Conflicts and Status Management"
parent: "Knowledge Base"
---

# Deployment Conflicts and Status Management

## Problem

Multiple concurrent deployments can cause:
- **Resource conflicts**: Azure resources (like PostgreSQL) get locked
- **Unpredictable state**: Unknown which deployment is active
- **Traffic splitting**: Multiple revisions receiving traffic simultaneously
- **Failed deployments**: "ServerIsBusy" errors when resources are locked

## Current Situation

### Active Revision (Stabilized)

**Revision**: `staging-env-api--0000115`  
**Created**: 2025-12-31T18:57:26+00:00  
**Status**: Active, 100% traffic  
**Image**: `ghcr.io/zimaxnet/engram/backend:latest`  
**Configuration**:
- `AUTH_REQUIRED`: `false`
- `CORS_ORIGINS`: `["https://engram.work","http://localhost:5173","http://localhost:5174"]`

This revision includes:
- ✅ Authentication fix (standard JWT validation) - commit `7ded10394`
- ✅ CORS preflight middleware - commit `9c462195c`
- ✅ Enhanced logging and diagnostics

**Previous Revision**: `staging-env-api--0000114` has been deactivated to prevent conflicts.

### Recent Deployment History

| Time | Status | Commit | Description |
|------|--------|--------|-------------|
| 18:52:44 | ❌ Failed | 8a09afb | Docs - Database busy |
| 18:51:32 | ❌ Failed | 8a09afb | Docs - Database busy |
| 18:49:58 | ✅ Success | 8a09afb | Docs - Succeeded |
| 18:33:01 | ✅ Success | 7ded103 | Auth fix - Succeeded |
| 17:24:13 | ✅ Active | ~7ded103 | **Currently Active** |

### Deployment Failures

Recent failures were caused by:
```
ERROR: ServerIsBusy
Cannot complete operation while server 'staging-env-db' is busy 
processing another operation. Try again later.
```

This happens when multiple deployments try to modify PostgreSQL configuration simultaneously.

## Solution: Deployment Status Management

### Check Current Status

```bash
./scripts/check-deployment-status.sh
```

This script shows:
- Active revision and details
- Recent GitHub Actions deployments
- All revisions and their status
- Traffic weight distribution
- Conflicts (multiple active revisions)

### Wait for Deployments to Complete

**Rule**: Wait ~14 minutes between deployments to avoid conflicts.

```bash
# Check if deployment is in progress
gh run list --workflow=Deploy --limit 1 --json status

# Wait for completion
gh run watch $(gh run list --workflow=Deploy --limit 1 --json databaseId -q '.[0].databaseId')
```

### Stabilize on Known Good Deployment

If you have multiple active revisions or conflicts:

1. **Identify the desired revision:**
   ```bash
   az containerapp revision list \
     --name staging-env-api \
     --resource-group engram-rg \
     --query "[].{name:name, active:properties.active, createdTime:properties.createdTime}" \
     -o table
   ```

2. **Set traffic to 100% on desired revision:**
   ```bash
   az containerapp ingress traffic set \
     --name staging-env-api \
     --resource-group engram-rg \
     --revision-weight <revision-name>=100
   ```

3. **Deactivate other revisions:**
   ```bash
   az containerapp revision deactivate \
     --name staging-env-api \
     --resource-group engram-rg \
     --revision <unwanted-revision-name>
   ```

### Prevent Future Conflicts

1. **Batch Changes**: Make all related changes in a single commit
2. **Wait Between Deployments**: ~14 minutes minimum
3. **Check Status First**: Use `check-deployment-status.sh` before deploying
4. **Monitor GitHub Actions**: Check for in-progress deployments

## Best Practices

### Before Committing

1. ✅ Review all changes: `git status` and `git diff`
2. ✅ Check deployment status: `./scripts/check-deployment-status.sh`
3. ✅ Ensure no deployments in progress
4. ✅ Batch related changes together

### After Committing

1. ✅ Wait for deployment to complete (~14 minutes)
2. ✅ Verify deployment succeeded: `gh run list --limit 1`
3. ✅ Check active revision: `az containerapp revision list`
4. ✅ Test the deployment

### Emergency: Stop All Deployments

If deployments are conflicting:

```bash
# Cancel in-progress workflows
gh run cancel $(gh run list --workflow=Deploy --limit 1 --json databaseId -q '.[0].databaseId')

# Wait for current deployment to finish
# Then stabilize on known good revision
```

## Current Recommendation

**Active revision `staging-env-api--0000114` is stable and healthy.**

This revision includes:
- ✅ Authentication fix (standard JWT validation)
- ✅ CORS preflight middleware
- ✅ Enhanced logging

**Action**: Wait for any in-progress deployments to complete, then verify this revision is still active and working correctly.

---

**Last Updated**: 2025-12-31  
**Status**: Monitoring deployment conflicts

