# Zep Cloud Migration Status

## Completed ✅

1. **Zep API Key Added to Key Vault**
   - Secret name: `zep-api-key`
   - Key Vault: `staging-env-kv-v2-soxm5`
   - Status: Successfully stored and enabled

2. **Bicep Templates Updated**
   - `infra/main.bicep` updated to use Zep Cloud (`https://app.getzep.com`)
   - Zep container module commented out (no longer needed)
   - Backend and Worker modules now reference `zepApiUrl` variable pointing to Zep Cloud

## Pending ⏳

**Container App Environment Variable Update**

The direct CLI update to change `ZEP_API_URL` from the self-hosted container to Zep Cloud is blocked by a container registry authentication issue. The update command triggers a new revision which requires pulling the container image, but the GitHub Container Registry authentication is failing.

### Current State
- **Backend API**: Still pointing to `https://zep.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Worker**: Still pointing to self-hosted Zep container
- **Bicep Template**: Updated to use `https://app.getzep.com` (will apply on next deployment)

## Solution Options

### Option 1: Next Deployment (Recommended)
The Bicep template is already updated. The next GitHub Actions deployment will automatically:
- Deploy containers with `ZEP_API_URL=https://app.getzep.com`
- Use the Zep API key from Key Vault
- Remove dependency on the self-hosted Zep container

**Action**: Trigger a deployment via GitHub Actions or wait for the next commit.

### Option 2: Manual Update via Azure Portal
1. Go to Azure Portal → Container Apps → `engram-api`
2. Navigate to "Revision management" → "Create new revision"
3. Edit environment variables
4. Change `ZEP_API_URL` to `https://app.getzep.com`
5. Create revision (may still have registry auth issues)

### Option 3: Fix Registry Authentication First
Update the registry password secret in the container app, then retry the CLI update:

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

## Verification

Once updated, verify the configuration:

```bash
# Check backend Zep URL
az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"

# Check backend logs for Zep initialization
az containerapp logs show \
  --name engram-api \
  --resource-group engram-rg \
  --tail 100 \
  | grep -i zep

# Should see: "Zep client initialized: https://app.getzep.com"
```

## Next Steps

1. **Immediate**: The Zep API key is in Key Vault and ready to use
2. **Next Deployment**: Bicep templates will automatically use Zep Cloud
3. **Optional**: Remove the self-hosted Zep container app after verifying Zep Cloud works:
   ```bash
   az containerapp delete \
     --name zep \
     --resource-group engram-rg \
     --yes
   ```

