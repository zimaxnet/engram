# Zep Cloud Migration Guide

## Current Situation

**Problem**: The deployment is currently using a self-hosted Zep container instead of Zep Cloud (`app.getzep.com`).

- **Currently deployed**: `https://zep.calmgrass-018b2019.eastus2.azurecontainerapps.io` (self-hosted container)
- **Should be**: `https://app.getzep.com` (Zep Cloud)

## Quick Fix: Update Running Containers

### Step 1: Update Backend API Container App

```bash
az containerapp update \
  --name engram-api \
  --resource-group engram-rg \
  --set-env-vars ZEP_API_URL=https://app.getzep.com
```

### Step 2: Update Worker Container App

```bash
az containerapp update \
  --name engram-worker \
  --resource-group engram-rg \
  --set-env-vars ZEP_API_URL=https://app.getzep.com
```

### Step 3: Verify the Change

```bash
# Check backend
az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"

# Check worker
az containerapp show \
  --name engram-worker \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"
```

### Step 4: Verify Zep API Key is in Key Vault

```bash
az keyvault secret show \
  --vault-name engram-kv \
  --name zep-api-key \
  --query "{enabled:attributes.enabled, contentType:contentType}"
```

If the secret doesn't exist, add it:
```bash
az keyvault secret set \
  --vault-name engram-kv \
  --name zep-api-key \
  --value "<your-zep-cloud-api-key>"
```

### Step 5: Remove Zep Container App (Optional)

Once verified that everything works with Zep Cloud, you can remove the self-hosted container:

```bash
az containerapp delete \
  --name zep \
  --resource-group engram-rg \
  --yes
```

## Long-term Fix: Update Bicep Templates

To make future deployments use Zep Cloud by default, update the Bicep templates:

### Option 1: Make Zep Container Optional (Recommended)

Modify `infra/main.bicep` to conditionally deploy the Zep container:

```bicep
@description('Use Zep Cloud instead of self-hosted container.')
param useZepCloud bool = true

@description('Zep Cloud API URL (if useZepCloud is true).')
param zepCloudUrl string = 'https://app.getzep.com'

// Conditionally deploy Zep container
module zepModule 'modules/zep-aca.bicep' = if (!useZepCloud) {
  name: 'zep'
  params: {
    // ... existing params
  }
}

// Use Zep Cloud URL or container URL
var zepApiUrl = useZepCloud ? zepCloudUrl : zepModule.outputs.zepApiUrl

// Backend uses zepApiUrl variable
module backendModule 'modules/backend-aca.bicep' = {
  // ...
  params: {
    zepApiUrl: zepApiUrl
    // ...
  }
}
```

### Option 2: Remove Zep Container Module Entirely

If you're committed to Zep Cloud, remove the Zep container module from `infra/main.bicep`:

1. Remove or comment out the `zepModule` section
2. Update `backendModule` and `workerModule` to use `zepCloudUrl` directly:

```bicep
@description('Zep Cloud API URL.')
param zepCloudUrl string = 'https://app.getzep.com'

module backendModule 'modules/backend-aca.bicep' = {
  // ...
  params: {
    zepApiUrl: zepCloudUrl  // Use Zep Cloud URL directly
    // ...
  }
}
```

## Testing

After updating, test the connection:

```bash
# Check backend logs for Zep initialization
az containerapp logs show \
  --name engram-api \
  --resource-group engram-rg \
  --tail 100 \
  | grep -i zep

# Look for: "Zep client initialized: https://app.getzep.com"
```

## Rollback

If you need to rollback to the self-hosted container:

```bash
# Get the Zep container FQDN
ZEP_FQDN=$(az containerapp show \
  --name zep \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# Update backend to use container
az containerapp update \
  --name engram-api \
  --resource-group engram-rg \
  --set-env-vars ZEP_API_URL=https://${ZEP_FQDN}
```

