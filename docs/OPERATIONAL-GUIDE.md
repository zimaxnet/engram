# Operational Guide

## Frontend Static Web App - No Site Issue

### Current Status
- **Static Web App Name**: `staging-env-web`
- **Default Hostname**: `calm-smoke-06afc910f.3.azurestaticapps.net`
- **Status**: Returns HTTP 301 (redirect) - no content deployed
- **Build ID**: None (no builds have been deployed)
- **Repository URL**: Not connected in Azure portal (but deployment uses GitHub Actions)

### Root Cause
The Static Web App exists but has no deployed content. The deployment workflow (`.github/workflows/deploy.yml`) uses the `Azure/static-web-apps-deploy@v1` action to upload built files, but either:
1. The workflow hasn't run successfully
2. The build step failed
3. The upload step failed silently

### Solution

#### Option 1: Trigger Manual Deployment via GitHub Actions
```bash
# Check if workflow has run
gh workflow view deploy.yml

# Trigger workflow manually
gh workflow run deploy.yml
```

#### Option 2: Manual Upload via Azure CLI
```bash
# Build frontend locally
cd frontend
npm install
npm run build

# Get deployment token
TOKEN=$(az staticwebapp secrets list \
  --name staging-env-web \
  --resource-group engram-rg \
  --query "properties.apiKey" -o tsv)

# Upload build output
cd dist
az staticwebapp deploy \
  --name staging-env-web \
  --resource-group engram-rg \
  --api-key $TOKEN \
  --source .
```

#### Option 3: Connect SWA to GitHub (if not connected)
The Bicep template sets `repositoryUrl` and `branch`, but Azure may require manual connection:
1. Go to Azure Portal → Static Web App → Deployment Center
2. Connect to GitHub repository
3. Configure build settings (app_location: `/frontend`, output_location: `/frontend/dist`)

---

## Container Scale-Up Procedure (0 to 1 Replicas)

### Current Configuration
All Container Apps are configured with **scale-to-zero**:
- **Backend API**: `minReplicas: 0`, `maxReplicas: 10`
- **Worker**: `minReplicas: 0`, `maxReplicas: 5`
- **Zep**: `minReplicas: 0`, `maxReplicas: 3`
- **Temporal**: `minReplicas: 0`, `maxReplicas: 2`

### Automatic Scale-Up
Container Apps automatically scale from 0 to 1 when they receive a request. The first request will experience a **cold start delay** (typically 10-30 seconds).

### Manual Scale-Up Methods

#### Method 1: HTTP Request (Recommended)
Simply make a request to the container app endpoint:
```bash
# Backend API
curl https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io/health

# Zep
curl https://zep.calmgrass-018b2019.eastus2.azurecontainerapps.io/healthz
```

#### Method 2: Azure CLI - Activate Revision
```bash
# Get latest revision
REVISION=$(az containerapp revision list \
  --name engram-api \
  --resource-group engram-rg \
  --query "[0].name" -o tsv)

# Activate (triggers scale-up)
az containerapp revision activate \
  --name engram-api \
  --resource-group engram-rg \
  --revision $REVISION
```

#### Method 3: Temporarily Set minReplicas to 1
```bash
# Update scale configuration
az containerapp update \
  --name engram-api \
  --resource-group engram-rg \
  --min-replicas 1

# Scale back down when done
az containerapp update \
  --name engram-api \
  --resource-group engram-rg \
  --min-replicas 0
```

#### Method 4: Using Bicep/ARM Template
Update the `minReplicas` value in the Bicep template and redeploy:
```bicep
scale: {
  minReplicas: 1  // Change from 0 to 1
  maxReplicas: 10
}
```

### Cold Start Considerations
- **First request delay**: 10-30 seconds
- **Subsequent requests**: Normal latency (< 1 second)
- **Health checks**: The deployment workflow includes retry logic (10 attempts, 10s delay) to handle cold starts

### Monitoring Scale Status
```bash
# Check current replicas
az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "{RunningReplicas:properties.runningStatus, MinReplicas:properties.template.scale.minReplicas}"

# List revisions and their replica counts
az containerapp revision list \
  --name engram-api \
  --resource-group engram-rg \
  --query "[].{Name:name, Active:properties.active, Replicas:properties.replicas}"
```

---

## Zep Configuration

### Current Setup: **Zep Cloud API** (`app.getzep.com`)

We are configured to use the **hosted Zep Cloud API** at `app.getzep.com`, not a self-hosted container.

### Configuration Details

#### Zep Cloud API
- **Endpoint**: `https://app.getzep.com`
- **Service**: Hosted Zep Cloud (managed by Zep)
- **Authentication**: API key required (stored in Azure Key Vault)

#### Backend Configuration
The backend should be configured to use Zep Cloud via environment variable:
```python
# backend/core/config.py
zep_api_url: str = Field("http://localhost:8000", alias="ZEP_API_URL")

# Should be set in Azure Container App to:
ZEP_API_URL: https://app.getzep.com
ZEP_API_KEY: <stored in Key Vault as 'zep-api-key'>
```

### Current Issue: Mismatch in Deployment

**Problem**: The current deployment is pointing to a self-hosted Zep container instead of Zep Cloud:
- **Currently deployed**: `https://zep.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Should be**: `https://app.getzep.com`

### Fix: Update to Zep Cloud

To switch from the self-hosted container to Zep Cloud:

#### Local Development
For local development, `docker-compose.yml` runs a Zep container:
```yaml
zep:
  image: zepai/zep:latest
  ports:
    - "8000:8000"
  environment:
    ZEP_POSTGRES_DSN: "postgres://postgres:password@postgres:5432/engram"
```

### Why Zep Cloud vs Self-Hosted Container?

**Advantages of Zep Cloud:**
- ✅ Fully managed service (no maintenance)
- ✅ No cold start delays
- ✅ Automatic scaling and updates
- ✅ Enterprise support available
- ✅ No infrastructure to manage

**Disadvantages:**
- ❌ External dependency
- ❌ Data stored in Zep's infrastructure
- ❌ Usage-based pricing

### Steps to Fix: Update to Zep Cloud

1. **Verify Zep Cloud API Key in Key Vault**:
   ```bash
   az keyvault secret show \
     --vault-name engram-kv \
     --name zep-api-key \
     --query value -o tsv
   ```

2. **Update Backend Container App to use Zep Cloud**:
   ```bash
   az containerapp update \
     --name engram-api \
     --resource-group engram-rg \
     --set-env-vars ZEP_API_URL=https://app.getzep.com
   ```

3. **Update Worker Container App**:
   ```bash
   az containerapp update \
     --name engram-worker \
     --resource-group engram-rg \
     --set-env-vars ZEP_API_URL=https://app.getzep.com
   ```

4. **Verify the change**:
   ```bash
   az containerapp show \
     --name engram-api \
     --resource-group engram-rg \
     --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"
   ```

5. **Remove Zep Container App** (no longer needed):
   ```bash
   az containerapp delete \
     --name zep \
     --resource-group engram-rg \
     --yes
   ```

6. **Update Bicep Templates** (for future deployments):
   - Modify `infra/main.bicep` to skip Zep container deployment
   - Update `infra/modules/backend-aca.bicep` to use `https://app.getzep.com` as default
   - Update `infra/modules/worker-aca.bicep` similarly

### Verifying Zep Cloud Connection

```bash
# Check backend Zep configuration
az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ZEP_API_URL' || name=='ZEP_API_KEY']"

# Test Zep Cloud API (requires API key)
curl -H "Authorization: Bearer <your-zep-api-key>" \
  https://app.getzep.com/api/v2/health

# Check backend logs for Zep connection
az containerapp logs show \
  --name engram-api \
  --resource-group engram-rg \
  --tail 50 \
  | grep -i zep

# Verify API key is in Key Vault
az keyvault secret show \
  --vault-name engram-kv \
  --name zep-api-key \
  --query "attributes.enabled"
```

---

## Quick Reference Commands

### Frontend Deployment
```bash
# Check SWA status
az staticwebapp show --name staging-env-web --resource-group engram-rg

# Trigger GitHub Actions deployment
gh workflow run deploy.yml

# Manual upload (after building)
cd frontend && npm run build
az staticwebapp deploy --name staging-env-web --resource-group engram-rg --api-key $TOKEN --source dist
```

### Container Scale-Up
```bash
# Trigger scale-up via HTTP
curl https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io/health

# Check replica status
az containerapp show --name engram-api --resource-group engram-rg --query "properties.runningStatus"

# Force scale-up (set min to 1)
az containerapp update --name engram-api --resource-group engram-rg --min-replicas 1
```

### Zep Cloud Verification
```bash
# Check backend Zep config
az containerapp show --name engram-api --resource-group engram-rg --query "properties.template.containers[0].env[?name=='ZEP_API_URL']"

# Verify API key in Key Vault
az keyvault secret show --vault-name engram-kv --name zep-api-key --query "attributes.enabled"

# Test Zep Cloud API (replace with your API key)
curl -H "Authorization: Bearer <api-key>" https://app.getzep.com/api/v2/health
```

