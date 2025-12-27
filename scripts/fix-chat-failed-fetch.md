# Fix "Failed to fetch" Chat Error

## Problem
Chat is showing "Failed to fetch" error from Elena. This indicates the frontend cannot connect to the backend API.

## Root Causes

### 1. Frontend API URL Not Set Correctly
The frontend bundle has `VITE_API_URL` baked in at build time. If the frontend was built with the wrong URL, it won't be able to connect.

**Check:**
- What URL is the frontend using? (Check browser console Network tab)
- Was the frontend rebuilt after backend URL changed?

### 2. CORS Configuration
Even though `CORS_ORIGINS` includes `*`, there might be a CORS issue.

**Check:**
- Browser console for CORS errors
- Backend CORS configuration

### 3. Authentication Issue
The health endpoint returns 401, which suggests authentication might be required even though `AUTH_REQUIRED=false`.

**Check:**
- Verify `AUTH_REQUIRED=false` in Container Apps
- Check if health endpoint requires auth (it shouldn't)

## Solutions

### Solution 1: Rebuild and Redeploy Frontend (Recommended)

The frontend needs to be rebuilt with the correct `VITE_API_URL`:

```bash
# Get the correct backend URL
BACKEND_URL=$(az containerapp show \
  --name staging-env-api \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "Backend URL: https://${BACKEND_URL}"

# Trigger GitHub Actions deployment
gh workflow run deploy.yml --field environment=staging
```

This will:
1. Build frontend with correct `VITE_API_URL`
2. Deploy to Static Web Apps
3. Ensure frontend can connect to backend

### Solution 2: Manual Frontend Rebuild

```bash
cd frontend

# Get backend URL
BACKEND_URL=$(az containerapp show \
  --name staging-env-api \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# Build with correct API URL
export VITE_API_URL="https://${BACKEND_URL}"
npm run build

# Deploy
TOKEN=$(az staticwebapp secrets list \
  --name staging-env-web \
  --resource-group engram-rg \
  --query "properties.apiKey" -o tsv)

cd dist
az staticwebapp deploy \
  --name staging-env-web \
  --resource-group engram-rg \
  --api-key "$TOKEN" \
  --source .
```

### Solution 3: Check Browser Console

Open browser DevTools (F12) at `https://engram.work` and check:
- **Console tab**: Look for JavaScript errors or "Failed to fetch" details
- **Network tab**: Check if API requests are being made and what the error is
- **Check the actual API URL** being used in failed requests

### Solution 4: Verify Backend is Accessible

```bash
# Test backend directly
curl -X POST "https://api.engram.work/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "Origin: https://engram.work" \
  -d '{"content": "Hello", "agent_id": "elena"}'
```

## Verification

After fixing:
1. Open `https://engram.work` in browser
2. Open DevTools (F12) → Network tab
3. Try sending a chat message
4. Verify the request goes to the correct backend URL
5. Check for successful response (HTTP 200)

## Current Status

- ✅ Backend is running
- ✅ `AZURE_AI_MODEL_ROUTER=model-router` is set
- ✅ `AUTH_REQUIRED=false` (should allow requests)
- ✅ CORS includes `*` (should allow all origins)
- ❓ Frontend `VITE_API_URL` may be incorrect or outdated

## Next Steps

1. **Immediate**: Check browser console to see what URL the frontend is trying to use
2. **Fix**: Rebuild and redeploy frontend with correct `VITE_API_URL`
3. **Verify**: Test chat functionality after redeployment

