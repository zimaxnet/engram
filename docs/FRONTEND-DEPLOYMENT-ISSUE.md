# Frontend Deployment Issue

## Problem
The site at `https://engram.work` shows an Azure Static Web Apps 404 page instead of the actual frontend application.

## Root Cause
The Static Web App has **no build ID**, meaning the deployment workflow completed but the files were never uploaded to the Static Web App.

## Symptoms
- Site shows: "Azure Static Web Apps - 404: Not found"
- Static Web App has `buildId: null`
- Deployment workflow shows "success" but files weren't deployed
- Local build works perfectly

## Solution Options

### Option 1: Re-trigger GitHub Actions Deployment (Recommended)
```bash
gh workflow run deploy.yml --field environment=staging
```

This will:
1. Build the frontend with correct `VITE_API_URL`
2. Use the `Azure/static-web-apps-deploy@v1` action to upload files
3. Properly deploy to Static Web Apps

### Option 2: Install SWA CLI and Deploy
```bash
# Install SWA CLI
npm install -g @azure/static-web-apps-cli

# Deploy
cd frontend/dist
swa deploy . \
  --deployment-token <token> \
  --env production
```

### Option 3: Use Azure Portal
1. Go to Azure Portal → Static Web App → `staging-env-web`
2. Navigate to "Deployment Center"
3. Check deployment history
4. Manually trigger a deployment or check for errors

## Verification

After deployment, verify:
```bash
# Check if build ID exists
az staticwebapp show \
  --name staging-env-web \
  --resource-group engram-rg \
  --query "properties.buildId"

# Test the site
curl -I https://engram.work/
```

## Why This Happened

The GitHub Actions workflow uses:
- `action: "upload"` - Should upload pre-built files
- `app_location: "/frontend/dist"` - Points to build output
- `skip_app_build: true` - Uses pre-built files

Possible causes:
1. The `frontend/dist` directory wasn't present in the GitHub Actions workspace
2. The deployment token expired or was invalid
3. The upload step failed silently
4. File path issues in the workflow

## Prevention

1. **Add verification step** to workflow:
```yaml
- name: Verify Frontend Build
  run: |
    ls -la frontend/dist/
    test -f frontend/dist/index.html || exit 1
```

2. **Check deployment status** after upload:
```yaml
- name: Verify Deployment
  run: |
    BUILD_ID=$(az staticwebapp show \
      --name staging-env-web \
      --resource-group engram-rg \
      --query "properties.buildId" -o tsv)
    if [ -z "$BUILD_ID" ]; then
      echo "❌ Deployment failed - no build ID"
      exit 1
    fi
    echo "✅ Deployment successful - Build ID: $BUILD_ID"
```

