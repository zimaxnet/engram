# Testing VoiceLive on Azure Static Web App

This directory contains scripts to test VoiceLive functionality on the deployed Azure Static Web App.

## Scripts

### 1. `test-voicelive-azure.py` (Recommended)
Python script that automatically discovers Azure resources and tests voice endpoints.

**Usage:**
```bash
# Basic usage (auto-discovers resources)
python3 scripts/test-voicelive-azure.py

# Specify resource group and environment
python3 scripts/test-voicelive-azure.py engram-rg staging

# Manually specify backend URL
python3 scripts/test-voicelive-azure.py engram-rg staging https://your-backend-url
```

**Requirements:**
```bash
pip install httpx websockets
```

### 2. `test-voicelive-azure.sh`
Bash script that uses curl and Python for testing.

**Usage:**
```bash
./scripts/test-voicelive-azure.sh
```

**Environment Variables:**
- `RESOURCE_GROUP` - Azure resource group (default: `engram-rg`)
- `ENVIRONMENT` - Environment name (default: `staging`)
- `BACKEND_URL` - Override backend URL (optional)

## Tests Performed

1. **Voice Status Endpoint** - Tests `/api/v1/voice/status`
2. **Voice Config (Elena)** - Tests `/api/v1/voice/config/elena`
3. **Voice Config (Marcus)** - Tests `/api/v1/voice/config/marcus`
4. **WebSocket Connection** - Tests WebSocket connection for real-time voice interaction

## Authentication

If you get 401 errors, the backend may require authentication. Options:

### Option 1: Check if AUTH_REQUIRED is disabled
If `AUTH_REQUIRED=false` in the backend environment, endpoints should be accessible without authentication.

### Option 2: Use authentication token
If authentication is required, you may need to:
1. Get an authentication token (Entra ID token or dev token)
2. Modify the script to include the token in requests

Example with token:
```python
headers = {"Authorization": f"Bearer {token}"}
response = await client.get(url, headers=headers)
```

### Option 3: Test through the SWA
The Static Web App may handle authentication automatically. Test the voice functionality directly in the browser at:
- https://engram.work (or your SWA URL)

## Troubleshooting

### Backend not accessible
- Verify the Container App is running: `az containerapp show --name staging-env-api --resource-group engram-rg`
- Check the FQDN is correct
- Verify network/firewall rules allow access

### 401 Unauthorized
- Check if `AUTH_REQUIRED` is set in backend environment
- Verify CORS configuration allows your domain
- Check if authentication tokens are required

### WebSocket connection fails
- Verify the backend supports WebSocket connections
- Check if the endpoint path is correct: `/api/v1/voice/voicelive/{session_id}`
- Ensure the backend is configured for VoiceLive (check environment variables)

### VoiceLive not configured
- Verify `AZURE_VOICELIVE_ENDPOINT` is set
- Verify `AZURE_VOICELIVE_KEY` or Managed Identity is configured
- Check backend logs for VoiceLive configuration errors

## Expected Output

Successful test output should show:
```
✓ Voice status endpoint responded successfully
✓ Voice config endpoint responded successfully for elena
✓ Voice config endpoint responded successfully for marcus
✓ WebSocket connected successfully
✓ Response: agent_switched
```

## Next Steps

After successful tests:
1. Open the SWA in your browser
2. Navigate to the voice chat interface
3. Test voice interaction with Elena or Marcus
4. Verify audio streaming works correctly

