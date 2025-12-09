# VoiceLive WebSocket Test Setup

## Current Status

✅ **Backend WebSocket**: Working - connection established  
❌ **Azure VoiceLive**: 401 Authentication Error

## Issue

The backend can't authenticate with Azure VoiceLive because environment variables aren't set.

## Solution

### Step 1: Set Environment Variables

Before starting the backend, set these variables:

```bash
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
```

### Step 2: Restart Backend with Variables

```bash
# Stop current backend (Ctrl+C)

# Start with environment variables
source venv/bin/activate
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
PYTHONPATH=. uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload
```

Or use the start script (update it to include these vars):

```bash
./scripts/start-backend.sh
```

### Step 3: Test Again

```bash
source venv/bin/activate
python3 scripts/test-voicelive-websocket.py
```

## Expected Results

✅ WebSocket connects to backend  
✅ Agent switching works (Elena ↔ Marcus)  
✅ No 401 errors  
✅ VoiceLive session created successfully  

## Troubleshooting

### Still Getting 401?

1. **Verify key is correct**: Check Azure Portal → Your AI Services → Keys
2. **Check key permissions**: VoiceLive requires specific API access
3. **Verify endpoint**: Should be `https://{your-resource}.services.ai.azure.com`
4. **Check project name**: Must match your Azure AI Services project

### Check Backend Logs

Look for:
- Authentication errors
- Endpoint construction
- Key validation

### Test Configuration

```bash
source venv/bin/activate
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="your-key"
python3 << 'EOF'
import os
import sys
sys.path.insert(0, 'backend')
os.environ.setdefault('ENVIRONMENT', 'development')
# ... other env vars ...
from backend.voice.voicelive_service import voicelive_service
print(f"Endpoint: {voicelive_service.endpoint}")
print(f"Key set: {bool(voicelive_service.settings.azure_openai_key)}")
EOF
```

## Next Steps After Success

1. ✅ Test agent switching
2. ✅ Test audio streaming
3. ✅ Update frontend to use VoiceLive
4. ✅ Full integration testing

