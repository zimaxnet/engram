# VoiceLive Token Generation Validation Results

**Date**: 2026-01-07  
**Environment**: Azure Staging  
**Backend URL**: `https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io`

## Test Results

### ✅ Health Check
- **Status**: PASSED
- **Endpoint**: `/health`
- **Response**: 200 OK

### ❌ Token Generation
- **Status**: FAILED
- **Endpoint**: `/api/v1/voice/realtime/token`
- **Request**:
  ```json
  {
    "agent_id": "elena",
    "modalities": ["video", "text"]
  }
  ```
- **Response**: 502 Bad Gateway
- **Error**: `"Failed to get ephemeral token: API version not supported"`

## Backend Logs Analysis

From Azure Container App logs:

```
"Requesting ephemeral token from: https://zimax.services.ai.azure.com/api/projects/zimax/openai/realtime/client_secrets"
"Using API version: 2025-10-01"
"Using project: zimax"
"Token request failed: 400\nURL: https://zimax.services.ai.azure.com/api/projects/zimax/openai/realtime/client_secrets\nError: API version not supported"
```

## Root Cause Analysis

### Issue Identified

The code is attempting to use the REST endpoint `/api/projects/{project}/openai/realtime/client_secrets` for a **unified endpoint with a project**, but this endpoint:

1. **Does not support project-based unified endpoints**
2. **May not support API version `2025-10-01`** for this endpoint type

### Expected Behavior

For unified endpoints with projects, the failsafe function should:

1. **Strategy 1**: Try Managed Identity token (current API version)
2. **Strategy 2**: Try Managed Identity token (fallback API versions)
3. **Strategy 3**: Use API key directly for WebSocket authentication (no REST call)
4. **Strategy 4**: Skip (only for direct endpoints)
5. **Strategy 5**: Skip (only for direct endpoints)

### Current Behavior

The logs show:
- ❌ No "🔄 Starting failsafe token generation..." log message
- ❌ Direct attempt to use REST endpoint `/client_secrets`
- ❌ Error: "API version not supported"

This suggests one of:
1. The failsafe function is not being called
2. The failsafe function is failing before logging
3. The code is falling back to old logic that tries REST endpoint

## Configuration Verification

### ✅ Environment Variables
- `AZURE_VOICELIVE_KEY`: Configured (secret reference: `voicelive-api-key`)
- `AZURE_VOICELIVE_API_VERSION`: `2025-10-01`
- `AZURE_VOICELIVE_ENDPOINT`: `https://zimax.services.ai.azure.com` (unified endpoint)
- `AZURE_VOICELIVE_PROJECT`: `zimax` (project-based)

### ✅ Managed Identity
- Available in Azure Container Apps
- Should work for Strategy 1 and 2

## Recommendations

### Immediate Actions

1. **Verify Code Deployment**
   - Confirm the latest code with failsafe function is deployed
   - Check git commit hash in container logs
   - Verify `_generate_token_with_failsafe` function exists

2. **Check Logging Level**
   - Ensure INFO level logs are enabled
   - Verify "🔄 Starting failsafe token generation..." appears in logs

3. **Test Strategy 3 Directly**
   - Strategy 3 should work immediately for unified endpoints
   - It just returns the API key (no REST call)
   - If Strategy 3 isn't working, check API key retrieval

### Code Investigation

1. **Verify Failsafe Function is Called**
   - Add explicit log at start of `get_realtime_token`
   - Add explicit log before calling `_generate_token_with_failsafe`
   - Verify function signature matches

2. **Check API Key Retrieval**
   - Verify `os.getenv("AZURE_VOICELIVE_KEY")` works in container
   - Check if secret reference is resolved correctly
   - Test API key format

3. **Test Managed Identity**
   - Verify `DefaultAzureCredential()` works in container
   - Check token audience: `https://ai.azure.com/.default`
   - Test token retrieval

### Expected Fix

The failsafe function should:
1. ✅ Log "🔄 Starting failsafe token generation..."
2. ✅ Try Strategy 1 (Managed Identity)
3. ✅ Try Strategy 2 (Managed Identity with fallback versions)
4. ✅ Try Strategy 3 (API key - should succeed for unified endpoints)
5. ✅ Return token response

**Strategy 3 should succeed** because:
- Unified endpoints support API key authentication
- No REST call needed (direct WebSocket authentication)
- API key is configured in environment

## Next Steps

1. **Deploy Latest Code** (if not already deployed)
   ```bash
   git push  # Triggers deployment
   ```

2. **Monitor Logs After Deployment**
   ```bash
   az containerapp logs show \
     --name staging-env-api \
     --resource-group engram-rg \
     --tail 100 \
     --follow
   ```

3. **Re-run Validation**
   ```bash
   python3 scripts/validate-token-generation-azure.py \
     --environment staging \
     --agent elena \
     --modalities video,text
   ```

4. **If Still Failing**
   - Check if failsafe logs appear
   - Verify API key is accessible
   - Test Managed Identity token generation
   - Review code for any early returns or exceptions

## Test Script

The validation script is available at:
- `scripts/validate-token-generation-azure.py`

Usage:
```bash
# Basic test
python3 scripts/validate-token-generation-azure.py

# With Managed Identity auth
python3 scripts/validate-token-generation-azure.py --use-auth

# Custom environment
python3 scripts/validate-token-generation-azure.py \
  --environment staging \
  --agent elena \
  --modalities video,text
```

## Related Documentation

- [VoiceLive Failsafe Token Generation](./voicelive-failsafe-token-generation.md)
- [VoiceLive Configuration](../../05-knowledge-base/voicelive-configuration.md)
- [VoiceLive Breakthrough Summary](./voicelive-failsafe-breakthrough-summary.md)

