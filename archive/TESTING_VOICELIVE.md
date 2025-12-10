# Testing VoiceLive Integration - Step by Step

Follow these steps to test VoiceLive integration locally.

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `azure-ai-voicelive` - VoiceLive SDK
- All other backend dependencies

## Step 2: Configure Environment

Create or update `.env` in the project root:

```bash
# Azure AI Services (Unified)
AZURE_AI_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_AI_PROJECT_NAME=zimax
AZURE_OPENAI_KEY=cf23c3ed0f9d420dbd02c1e95a5b5bb3

# VoiceLive Configuration
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=en-US-Ava:DragonHDLatestNeural
MARCUS_VOICELIVE_VOICE=en-US-GuyNeural

# Required for backend
ENVIRONMENT=development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=engram
ZEP_API_URL=http://localhost:8000
TEMPORAL_HOST=localhost:7233
```

Or export them:
```bash
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
```

## Step 3: Test Basic Import

```bash
cd backend
python3 -c "
import sys
sys.path.insert(0, '.')
import os
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5432')
os.environ.setdefault('POSTGRES_USER', 'postgres')
os.environ.setdefault('POSTGRES_PASSWORD', 'password')
os.environ.setdefault('POSTGRES_DB', 'engram')
os.environ.setdefault('ZEP_API_URL', 'http://localhost:8000')
os.environ.setdefault('TEMPORAL_HOST', 'localhost:7233')

from voice.voicelive_service import voicelive_service
print('✓ VoiceLive service imported')
print('✓ Endpoint:', voicelive_service.endpoint)
print('✓ Elena instructions:', len(voicelive_service.get_elena_instructions()), 'chars')
print('✓ Marcus instructions:', len(voicelive_service.get_marcus_instructions()), 'chars')
"
```

Expected output:
```
✓ VoiceLive service imported
✓ Endpoint: https://zimax.services.ai.azure.com
✓ Elena instructions: XXX chars
✓ Marcus instructions: XXX chars
```

## Step 4: Start Backend Server

In one terminal:

```bash
cd backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8082
INFO:     Application startup complete.
```

## Step 5: Test WebSocket Connection

### Option A: Using Python

Install websockets:
```bash
pip install websockets
```

Test script:
```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8082/api/v1/voice/voicelive/test-session-123"
    
    async with websockets.connect(uri) as websocket:
        print("✓ Connected to VoiceLive WebSocket")
        
        # Switch to Elena
        await websocket.send(json.dumps({
            "type": "agent",
            "agent_id": "elena"
        }))
        print("→ Sent: switch to Elena")
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"← Received: {data}")
        
        # Switch to Marcus
        await websocket.send(json.dumps({
            "type": "agent",
            "agent_id": "marcus"
        }))
        print("→ Sent: switch to Marcus")
        
        response = await websocket.recv()
        data = json.loads(response)
        print(f"← Received: {data}")

asyncio.run(test())
```

### Option B: Using Browser Console

1. Open browser DevTools (F12)
2. Go to Console tab
3. Run:

```javascript
const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/test-123');

ws.onopen = () => {
    console.log('✓ Connected');
    ws.send(JSON.stringify({type: 'agent', agent_id: 'elena'}));
};

ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log('← Received:', data);
};

ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Disconnected');
```

## Step 6: Test Audio Streaming (Advanced)

For full audio testing, you'll need to:

1. Capture audio from microphone (PCM16, 24kHz, mono)
2. Encode to base64
3. Send via WebSocket
4. Receive and play audio responses

This is best done through the frontend component.

## Troubleshooting

### "ModuleNotFoundError: No module named 'azure.ai.voicelive'"
```bash
pip install azure-ai-voicelive
```

### "No module named 'backend'"
Make sure you're running from the project root or have PYTHONPATH set:
```bash
export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
```

### "Connection refused"
Make sure backend is running:
```bash
cd backend
uvicorn backend.api.main:app --reload
```

### "401 Unauthorized"
Check your `AZURE_OPENAI_KEY` is correct and has VoiceLive permissions.

## Success Criteria

✅ VoiceLive service imports without errors  
✅ Endpoint is constructed correctly  
✅ WebSocket accepts connections  
✅ Agent switching works  
✅ No import or configuration errors  

## Next Steps

Once basic tests pass:
1. Update frontend `VoiceChat.tsx` to use VoiceLive
2. Test full audio streaming
3. Deploy to Azure and test in production

