# Voice Connection Test Results

## Test Date
2025-12-27

## Issue
Voice connection failing with "Failed to fetch" error in the browser when trying to connect to voice functionality.

## Diagnostic Results

### 1. Backend Configuration
- **Backend URL**: `https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io`
- **SWA URL**: `https://engram.work`
- **CORS_ORIGINS**: `["https://engram.work", "https://*.azurestaticapps.net", "http://localhost:5173", "*"]` ✓
- **AUTH_REQUIRED**: Set to `false` ✓

### 2. Endpoint Tests
All endpoints are returning **401 Unauthorized**:
- `/health` - 401 ❌
- `/api/v1/voice/status` - 401 ❌
- `/api/v1/voice/config/elena` - 401 ❌
- `/api/v1/voice/config/marcus` - 401 ❌
- `/api/v1/voice/realtime/token` - 401 ❌

### 3. Root Cause Analysis

The fact that even the `/health` endpoint (which has no authentication dependencies) is returning 401 suggests one of the following:

1. **Container hasn't restarted** with the new `AUTH_REQUIRED=false` setting
2. **Azure Container Apps ingress** may have authentication enabled
3. **Global middleware** is enforcing authentication before routes are reached
4. **Environment variable** not being read correctly by the application

## Actions Taken

1. ✅ Set `AUTH_REQUIRED=false` via Azure CLI
2. ✅ Restarted the container revision
3. ✅ Verified environment variable is set correctly
4. ❌ Endpoints still returning 401

## Next Steps

### Option 1: Check Azure Container Apps Ingress Auth
Azure Container Apps may have ingress-level authentication enabled:

```bash
az containerapp ingress show \
  --name staging-env-api \
  --resource-group engram-rg \
  --query "customDomains"
```

If there's authentication at the ingress level, it needs to be disabled or configured to allow the SWA domain.

### Option 2: Verify Container Logs
Check if the application is actually reading `AUTH_REQUIRED=false`:

```bash
az containerapp logs show \
  --name staging-env-api \
  --resource-group engram-rg \
  --tail 100 \
  --type console | grep -i "auth_required\|starting\|environment"
```

### Option 3: Force New Revision
Create a new revision to ensure the environment variable is picked up:

```bash
# Trigger a new deployment
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars 'AUTH_REQUIRED=false' \
  --revision-suffix $(date +%s)
```

### Option 4: Check Application Code
Verify that the application is correctly reading the environment variable. The code in `backend/core/config.py` should parse `AUTH_REQUIRED` as a boolean.

### Option 5: Test with Authentication Token
If authentication is required, implement token-based auth in the frontend:

1. Get an authentication token (Entra ID or dev token)
2. Store it in localStorage
3. Send it with API requests

The API client already supports this - it reads from `localStorage.getItem('auth_token')`.

## Test Scripts Created

1. **`scripts/test-voicelive-azure.py`** - Comprehensive test script for voice endpoints
2. **`scripts/test-voicelive-azure.sh`** - Bash version of the test script
3. **`scripts/diagnose-voice-connection.sh`** - Diagnostic script for troubleshooting

## Recommendations

1. **Immediate**: Check Azure Container Apps ingress configuration for authentication
2. **Short-term**: Verify container logs show `AUTH_REQUIRED=false` is being read
3. **Long-term**: Implement proper authentication flow in the frontend for production use

## Status
🔴 **BLOCKED** - All endpoints returning 401, preventing voice connection testing.

