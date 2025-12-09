# Testing VoiceLive Integration Locally

This guide walks you through testing the VoiceLive integration for both Elena and Marcus agents.

## Prerequisites

1. **Python 3.11+** installed
2. **Azure credentials** configured in `.env`
3. **Backend dependencies** installed

## Step 1: Install VoiceLive SDK

```bash
cd backend
pip install azure-ai-voicelive
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment

Create or update `.env` file in the project root:

```env
# Azure AI Services (Unified)
AZURE_AI_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_AI_PROJECT_NAME=zimax
AZURE_OPENAI_KEY=your-key-here

# VoiceLive Configuration
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=en-US-Ava:DragonHDLatestNeural
MARCUS_VOICELIVE_VOICE=en-US-GuyNeural

# Other required variables
ENVIRONMENT=development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=engram
ZEP_API_URL=http://localhost:8000
TEMPORAL_HOST=localhost:7233
```

## Step 3: Run Basic Tests

Test the VoiceLive service configuration:

```bash
python3 scripts/test-voicelive.py
```

This will verify:
- ✓ VoiceLive service imports correctly
- ✓ Configuration is valid
- ✓ Endpoint construction works
- ✓ Credentials are set up
- ✓ Elena and Marcus instructions are loaded

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

### Option A: Using the Test Script

```bash
python3 scripts/test-voicelive.py --connection
```

### Option B: Using a WebSocket Client

Install a WebSocket client:
```bash
pip install websockets
```

Create a test client script:

```python
import asyncio
import websockets
import json

async def test_voicelive():
    uri = "ws://localhost:8082/api/v1/voice/voicelive/test-session-123"
    
    async with websockets.connect(uri) as websocket:
        print("✓ Connected to VoiceLive WebSocket")
        
        # Switch to Elena
        await websocket.send(json.dumps({
            "type": "agent",
            "agent_id": "elena"
        }))
        
        # Wait for confirmation
        response = await websocket.recv()
        print(f"Response: {response}")
        
        # Switch to Marcus
        await websocket.send(json.dumps({
            "type": "agent",
            "agent_id": "marcus"
        }))
        
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(test_voicelive())
```

### Option C: Using Browser DevTools

1. Open browser console
2. Run:
```javascript
const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/test-123');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.send(JSON.stringify({type: 'agent', agent_id: 'elena'}));
```

## Step 6: Test Audio Streaming

For full audio testing, you'll need to:

1. **Capture audio** from microphone (PCM16, 24kHz, mono)
2. **Encode to base64** and send via WebSocket
3. **Receive audio** responses and play them

This requires browser APIs or a desktop application. The frontend `VoiceChat` component will handle this.

## Step 7: Verify Agent Switching

Test switching between Elena and Marcus:

```python
import asyncio
import websockets
import json

async def test_agent_switching():
    uri = "ws://localhost:8082/api/v1/voice/voicelive/test-switch"
    
    async with websockets.connect(uri) as websocket:
        # Start with Elena
        await websocket.send(json.dumps({
            "type": "agent",
            "agent_id": "elena"
        }))
        response = await websocket.recv()
        data = json.loads(response)
        assert data.get("agent_id") == "elena"
        print("✓ Switched to Elena")
        
        # Switch to Marcus
        await websocket.send(json.dumps({
            "type": "agent",
            "agent_id": "marcus"
        }))
        response = await websocket.recv()
        data = json.loads(response)
        assert data.get("agent_id") == "marcus"
        print("✓ Switched to Marcus")

asyncio.run(test_agent_switching())
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'azure.ai.voicelive'"

**Solution**: Install the SDK
```bash
pip install azure-ai-voicelive
```

### "VoiceLive endpoint not configured"

**Solution**: Set environment variables:
```bash
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="your-key"
```

### "Connection refused" when testing WebSocket

**Solution**: Make sure backend is running:
```bash
cd backend
uvicorn backend.api.main:app --reload
```

### "401 Unauthorized" or authentication errors

**Solution**: 
- Verify `AZURE_OPENAI_KEY` is correct
- Check the key has VoiceLive permissions
- Ensure endpoint format is correct

### Import errors in test script

**Solution**: Make sure you're running from project root:
```bash
cd /path/to/CogAI
python3 scripts/test-voicelive.py
```

## Expected Results

✅ VoiceLive service imports successfully  
✅ Configuration loads correctly  
✅ WebSocket endpoint accepts connections  
✅ Agent switching works  
✅ Audio messages are accepted (even if not processed yet)  
✅ Error handling works correctly  

## Next Steps

Once basic tests pass:

1. **Update Frontend**: Modify `VoiceChat.tsx` to use VoiceLive endpoint
2. **Test Audio**: Verify PCM16 audio streaming works
3. **Test Conversations**: Have actual voice conversations with both agents
4. **Deploy**: Test in Azure environment

## Additional Resources

- [VoiceLive Service Code](../backend/voice/voicelive_service.py)
- [Voice Router](../backend/api/routers/voice.py)
- [Local Testing Guide](local-testing.md)

