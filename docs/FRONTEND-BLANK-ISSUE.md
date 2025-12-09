# Frontend Blank Page Issue

## Problem
The frontend at `https://engram.work` is loading but showing a blank page.

## Root Cause
The deployed JavaScript bundle has a **hardcoded API URL** instead of using the `VITE_API_URL` environment variable:
- **Hardcoded in bundle**: `https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Should use**: Environment variable `VITE_API_URL` set during build

This means:
1. The frontend was built without the `VITE_API_URL` environment variable
2. The bundle defaulted to a hardcoded URL
3. The React app may be failing to connect to the API or encountering CORS errors

## Solution

### Option 1: Rebuild and Redeploy via GitHub Actions (Recommended)

The deployment workflow sets `VITE_API_URL` during build. Trigger a new deployment:

```bash
gh workflow run deploy.yml --field environment=staging
```

This will:
1. Build the frontend with the correct `VITE_API_URL` from infrastructure outputs
2. Deploy the new build to Static Web Apps

### Option 2: Manual Build and Deploy

If you need to deploy immediately:

```bash
# Get the backend URL
BACKEND_URL=$(az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# Build frontend with correct API URL
cd frontend
VITE_API_URL="https://${BACKEND_URL}" npm run build

# Get deployment token
TOKEN=$(az staticwebapp secrets list \
  --name staging-env-web \
  --resource-group engram-rg \
  --query "properties.apiKey" -o tsv)

# Deploy
cd dist
az staticwebapp deploy \
  --name staging-env-web \
  --resource-group engram-rg \
  --api-key $TOKEN \
  --source .
```

### Option 3: Check Browser Console

Open the browser developer console (F12) at `https://engram.work` and check for:
- Network errors (failed API requests)
- CORS errors
- JavaScript errors preventing React from rendering

## Verification

After redeploying, verify:
1. The page loads and shows the ENGRAM interface
2. Browser console has no errors
3. Network tab shows successful API calls to the backend
4. The JavaScript bundle uses the correct API URL (check source)

## Prevention

Ensure the deployment workflow always sets `VITE_API_URL`:
- The workflow already does this: `VITE_API_URL: ${{ needs.deploy-infra.outputs.backend_url }}`
- The issue was likely a failed or incomplete deployment
- Future deployments should work correctly

