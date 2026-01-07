# VoiceLive Video Configuration Testing

## Current Status

✅ **Backend Changes Complete**: Video routing is configured to bypass backend
✅ **Deployment Successful**: Changes are deployed to production
⚠️ **Token Endpoint Limitation**: Unified endpoints may not support REST token endpoint

## Test Results

### Token Endpoint Test
- **Status**: ❌ API version not supported
- **Error**: `"Failed to get ephemeral token: API version not supported"`
- **Endpoint**: `https://zimax.services.ai.azure.com/api/projects/zimax/openai/realtime/client_secrets`
- **API Version**: `2025-10-01`

### Known Limitations

**Unified Endpoints (`services.ai.azure.com`)**:
- ✅ **WebSocket Proxy**: Works (audio/transcripts through backend)
- ❌ **REST Token Endpoint**: May not be supported for project-based endpoints
- ⚠️ **Direct Video Connection**: Requires REST token endpoint (may not work)

**Direct Endpoints (`openai.azure.com`)**:
- ✅ **REST Token Endpoint**: Supported
- ✅ **WebSocket Proxy**: Also supported
- ✅ **Direct Video Connection**: Should work

## Testing Options

### Option 1: Test WebSocket Connection (Recommended)

Test if `video_connection` is included in `agent_switched` message:

```bash
# Connect to WebSocket endpoint
wscat -c "wss://engram.work/api/v1/voice/voicelive/test-session?token=YOUR_TOKEN"

# Expected response:
{
  "type": "agent_switched",
  "agent_id": "elena",
  "video_connection": {
    "token": "...",
    "endpoint": "wss://...",
    "modalities": ["video", "text"]
  }
}
```

### Option 2: Test Token Endpoint Directly

Try different API versions:

```bash
# Try 2024-10-01-preview (legacy)
curl -X POST "https://engram.work/api/v1/voice/realtime/token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "agent_id": "elena",
    "modalities": ["video", "text"]
  }'
```

### Option 3: Check Backend Logs

```bash
# Check if video_connection is being generated
az containerapp logs show \
  --name <app-name> \
  --resource-group engram-rg \
  --tail 100 \
  --type console | grep -i "video_connection\|video token"
```

## Workaround: Use WebSocket Proxy for Video

If REST token endpoint doesn't work, we can:

1. **Keep video through backend WebSocket** (current implementation)
2. **Optimize video chunk handling** (reduce backend load)
3. **Use direct connection only when available** (fallback to proxy)

## Next Steps

1. **Verify WebSocket `video_connection`**: Check if `agent_switched` message includes video connection info
2. **Test with different API version**: Try `2024-10-01-preview` if `2025-10-01` doesn't work
3. **Check Azure documentation**: Verify if project-based unified endpoints support `/client_secrets`
4. **Frontend implementation**: Implement direct video connection if token works, otherwise use WebSocket proxy

## Configuration Check

Verify current configuration:

```bash
# Check API version
az containerapp show \
  --name <app-name> \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AZURE_VOICELIVE_API_VERSION'].value" -o tsv

# Check endpoint
az containerapp show \
  --name <app-name> \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AZURE_VOICELIVE_ENDPOINT'].value" -o tsv
```

