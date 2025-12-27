# Working VoiceLive Configuration for SWA Deployment

## Summary

This document describes the tested and working VoiceLive configuration for the deployed Static Web App (SWA) at `https://engram.work`.

## Current Configuration

### Backend API
- **URL**: `https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io`
- **AUTH_REQUIRED**: `false` (for POC/testing)
- **CORS_ORIGINS**: `["https://engram.work", "https://*.azurestaticapps.net", "http://localhost:5173", "*"]`

### VoiceLive Configuration
- **Endpoint**: `https://zimax.services.ai.azure.com` (Unified endpoint)
- **Model**: `gpt-realtime`
- **Project Name**: `zimax` (optional, for project-based endpoints)
- **API Version**: `2024-10-01-preview`

## Working Endpoints

### ✅ REST Endpoints (Working)

1. **Voice Status**
   ```
   GET /api/v1/voice/status
   ```
   - Returns VoiceLive configuration status
   - Shows active sessions and available agents

2. **Voice Config**
   ```
   GET /api/v1/voice/config/{agent_id}
   ```
   - Returns agent-specific voice configuration
   - Includes voice name, model, and endpoint status

### ⚠️ REST Endpoints (Not Supported with Unified Endpoint)

3. **Token Endpoint** (Not Available)
   ```
   POST /api/v1/voice/realtime/token
   ```
   - **Status**: Returns 404 "Resource not found"
   - **Reason**: Unified endpoints (`services.ai.azure.com`) do not support the `/openai/realtime/client_secrets` REST endpoint
   - **Workaround**: Use WebSocket proxy endpoint instead

### ✅ WebSocket Endpoint (Recommended)

4. **WebSocket Proxy** (Works with Unified Endpoint)
   ```
   WS /api/v1/voice/voicelive/{session_id}
   ```
   - **Status**: ✅ Fully supported
   - **How it works**: Backend handles VoiceLive connection internally
   - **Audio flow**: Browser → Backend WebSocket → Azure VoiceLive
   - **Benefits**: 
     - Works with unified endpoints
     - Backend handles authentication
     - Supports memory enrichment
     - Handles all VoiceLive events

## Frontend Implementation

### Recommended Approach: WebSocket Proxy

Since the unified endpoint doesn't support REST token endpoints, the frontend should use the WebSocket proxy:

```typescript
// Connect to backend WebSocket proxy
const ws = new WebSocket(
  `wss://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/voice/voicelive/${sessionId}`
);

// Send audio data
ws.send(audioData);

// Receive events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle: transcript, audio, visemes, etc.
};
```

### Alternative: Direct OpenAI Endpoint

If you need browser-direct token support, switch to a direct OpenAI endpoint:

**Configuration Change:**
```bash
AZURE_VOICELIVE_ENDPOINT=https://zimax.openai.azure.com
```

**Benefits:**
- REST token endpoint works
- Browser can connect directly to Azure
- Lower latency (no backend proxy)

**Trade-offs:**
- Requires direct OpenAI resource (not unified endpoint)
- Token management in frontend
- Less backend control over connection

## Testing

### Local Docker Test
```bash
# Build image
docker build -t engram-backend:local -f backend/Dockerfile backend/

# Run with VoiceLive config
docker run -d \
  --name engram-backend-test \
  -p 8082:8080 \
  -e ENVIRONMENT=development \
  -e AUTH_REQUIRED=false \
  -e AZURE_VOICELIVE_ENDPOINT="https://zimax.services.ai.azure.com" \
  -e AZURE_VOICELIVE_KEY="<key>" \
  -e AZURE_VOICELIVE_MODEL="gpt-realtime" \
  -e CORS_ORIGINS='["http://localhost:5173", "*"]' \
  engram-backend:local

# Test endpoints
curl http://localhost:8082/api/v1/voice/status
curl http://localhost:8082/api/v1/voice/config/elena
```

### Azure Deployment Test
```bash
# Test from command line
./scripts/test-swa-voicelive-working.sh
```

## CORS Configuration

The backend is configured to accept requests from:
- `https://engram.work` (SWA custom domain)
- `https://*.azurestaticapps.net` (SWA default domains)
- `http://localhost:5173` (local development)
- `*` (wildcard for testing)

**Production Recommendation**: Remove `*` wildcard and use specific domains only.

## Authentication

### Current (POC/Testing)
- `AUTH_REQUIRED=false`
- No authentication required
- Suitable for testing and POC

### Production
- `AUTH_REQUIRED=true`
- Frontend authenticates via SWA (Azure AD)
- Backend validates tokens
- Secure for production use

## Known Limitations

1. **Unified Endpoint Token Endpoint**
   - REST `/realtime/token` endpoint not available
   - Use WebSocket proxy instead
   - Or switch to direct OpenAI endpoint

2. **API Version**
   - Current: `2024-10-01-preview`
   - Project-based endpoints may require `2025-10-01`
   - Check Azure documentation for latest supported version

## Recommendations

### For Current Deployment (Unified Endpoint)
1. ✅ Use WebSocket proxy endpoint (`/api/v1/voice/voicelive/{session_id}`)
2. ✅ Backend handles all VoiceLive connections
3. ✅ Memory enrichment works automatically
4. ✅ All VoiceLive features supported

### For Future (If Token Support Needed)
1. Switch to direct OpenAI endpoint (`openai.azure.com`)
2. Update `AZURE_VOICELIVE_ENDPOINT` environment variable
3. Frontend can use token endpoint for browser-direct connections
4. Consider latency trade-offs (direct vs proxy)

## Verification Checklist

- [x] Backend API is accessible
- [x] CORS configured for SWA domain
- [x] VoiceLive endpoint configured
- [x] Voice status endpoint working
- [x] Voice config endpoint working
- [x] WebSocket proxy endpoint available
- [ ] Frontend updated to use WebSocket proxy (if not already)
- [ ] Authentication configured for production (AUTH_REQUIRED=true)
- [ ] CORS wildcard removed for production

## Next Steps

1. **Frontend Update** (if needed):
   - Ensure VoiceChat component uses WebSocket proxy
   - Update connection logic to use `/api/v1/voice/voicelive/{session_id}`
   - Remove token endpoint dependency

2. **Production Hardening**:
   - Set `AUTH_REQUIRED=true`
   - Remove `*` from CORS_ORIGINS
   - Enable authentication in SWA
   - Test end-to-end with authentication

3. **Monitoring**:
   - Monitor WebSocket connections
   - Track VoiceLive session health
   - Monitor memory enrichment success rate

## Support

For issues or questions:
- Check logs: `az containerapp logs show --name staging-env-api --resource-group engram-rg`
- Review SOP: `docs/sop/voicelive-configuration.md`
- Test script: `scripts/test-swa-voicelive-working.sh`

