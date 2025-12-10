# Fix: Update Containers to Use Zep Cloud

## Current Issue
The deployed container apps (`engram-api` and `engram-worker`) are still using the old Zep container URL:
- **Current**: `https://zep.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Should be**: `https://app.getzep.com`

## Root Cause
The Bicep template has been updated, but the running containers were deployed before the change. Updating environment variables directly via CLI fails due to:
1. Registry authentication issues (GitHub Container Registry token may be expired)
2. Update triggers new revision which requires image pull

## Solution: Deploy via GitHub Actions

The Bicep template is already updated to use Zep Cloud. A new deployment will:
1. ✅ Use the updated Bicep template with `zepApiUrl = 'https://app.getzep.com'`
2. ✅ Deploy containers with correct `ZEP_API_URL` environment variable
3. ✅ Have fresh registry credentials from GitHub Actions

## Verification After Deployment

```bash
# Check backend Zep URL
az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"

# Check worker Zep URL
az containerapp show \
  --name engram-worker \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"

# Should show: "https://app.getzep.com"
```

## Alternative: Manual Update (If Deployment Fails)

If the deployment fails, you can manually update the registry secret and then update the containers:

```bash
# Get a fresh GitHub token (PAT with package:read permission)
GITHUB_TOKEN="<your-github-pat>"

# Update registry password secret
az containerapp secret set \
  --name engram-api \
  --resource-group engram-rg \
  --secrets registry-password=$GITHUB_TOKEN

# Then update environment variable
az containerapp update \
  --name engram-api \
  --resource-group engram-rg \
  --set-env-vars ZEP_API_URL=https://app.getzep.com
```

## Status
- ✅ Bicep template updated
- ✅ Zep API key in Key Vault
- ⏳ Waiting for deployment to apply changes

