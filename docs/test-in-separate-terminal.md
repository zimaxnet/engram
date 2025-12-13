# Testing VoiceLive in a Separate Terminal

## Quick Steps

### Terminal 1 (Backend - Already Running)
Keep your backend running here. You should see:
```
INFO:     Application startup complete.
```

### Terminal 2 (Testing - New Terminal)

1. **Navigate to project directory:**
   ```bash
   cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/CogAI
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Run the test:**
   ```bash
   python3 scripts/test-voicelive-websocket.py
   ```

## One-Liner Command

You can also run it all in one command:

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/CogAI && source venv/bin/activate && python3 scripts/test-voicelive-websocket.py
```

## Alternative: Browser Console Test

If you prefer to test in the browser:

1. Open browser DevTools (F12)
2. Go to Console tab
3. Run:

```javascript
const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/test-123');
ws.onopen = () => {
  console.log('✓ Connected');
  ws.send(JSON.stringify({type: 'agent', agent_id: 'elena'}));
};
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Disconnected');
```

## Expected Output

If successful, you should see:
```
✓ WebSocket connected successfully
✓ Response: agent_switched (or similar)
```

If there's still a 401 error, check:
- Backend logs for authentication errors
- Azure credentials are set correctly
- VoiceLive is enabled in Azure Portal

