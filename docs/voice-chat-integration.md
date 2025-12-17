---
layout: default
title: Voice & Chat Integration
---

# [Home](/) › Voice & Chat Integration

# Voice & Chat Integration Guide

Engram provides two integrated communication channels for interacting with AI agents:

| Channel | Endpoint | Model | Auth | Use Case |
|---------|----------|-------|------|----------|
| **Chat** | API Gateway | gpt-5.1-chat | API Key | Text-based conversations |
| **Voice** | Azure AI Services | gpt-realtime | DefaultAzureCredential | Real-time voice interactions |

## Security Model (NIST AI RMF Compliant)

| Level | Environment | Chat Auth | VoiceLive Auth |
|-------|-------------|-----------|----------------|
| 1-2 | POC/Staging | API Key (APIM) | Azure CLI / DefaultAzureCredential |
| 3-5 | Production/Enterprise | API Key (APIM) | Managed Identity (DefaultAzureCredential) |

**DefaultAzureCredential** automatically selects the best credential for each environment:

- **Local Dev**: Azure CLI (`az login`)
- **Azure Container Apps**: Managed Identity
- **AKS**: Workload Identity
- **VMs**: System-assigned Managed Identity

---

## Chat Integration (API Gateway)

### Configuration

The chat system uses an OpenAI-compatible API gateway for text-based agent interactions.

```bash
# Environment Variables
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_KEY=<your-api-key>
AZURE_AI_DEPLOYMENT=gpt-5.1-chat
```

### API Endpoints

#### REST Chat (Single Turn)

```bash
POST /api/v1/chat
Content-Type: application/json

{
  "content": "What are the key requirements for this project?",
  "agent_id": "elena",
  "session_id": "optional-session-id"
}
```

**Response:**

```json
{
  "message_id": "uuid",
  "content": "Based on my analysis...",
  "agent_id": "elena",
  "agent_name": "Dr. Elena Vasquez",
  "timestamp": "2025-12-15T10:30:00Z",
  "session_id": "session-123"
}
```

#### WebSocket Chat (Streaming)

```javascript
// Connect to streaming chat
const ws = new WebSocket('ws://localhost:8082/api/v1/chat/ws/session-123');

// Send message
ws.send(JSON.stringify({
  type: 'message',
  content: 'Analyze project risks',
  agent_id: 'marcus'
}));

// Receive streaming response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'typing':
      // Agent is typing
      break;
    case 'chunk':
      // Append text chunk: data.content
      break;
    case 'complete':
      // Response finished: data.message_id
      break;
  }
};
```

### Agents

| Agent | ID | Expertise |
|-------|-----|-----------|
| **Elena** | `elena` | Business Analysis, Requirements Engineering |
| **Marcus** | `marcus` | Project Management, Risk Assessment |

---

## VoiceLive Integration (Real-time Voice)

### Configuration

VoiceLive provides real-time speech-to-speech conversations using Azure AI Services with **NIST AI RMF compliant authentication**.

```bash
# Environment Variables
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=en-US-Ava:DragonHDLatestNeural
MARCUS_VOICELIVE_VOICE=en-US-GuyNeural

# Optional: API key for POC/staging (not needed if using Azure CLI or Managed Identity)
# AZURE_VOICELIVE_KEY=<optional-for-poc-only>
```

### Authentication

VoiceLive uses `DefaultAzureCredential` which automatically selects the appropriate credential:

| Environment | Credential Used |
|-------------|-----------------|
| Local Development | Azure CLI (`az login`) |
| Azure Container Apps | Managed Identity |
| Azure Kubernetes Service | Workload Identity |
| Azure VMs | System Managed Identity |
| GitHub Actions | Federated Identity |

**Enterprise (Level 3-5)**: Managed Identity is required - no API keys in production.

### API Endpoints

#### Voice Configuration

```bash
GET /api/v1/voice/config/{agent_id}
```

**Response:**

```json
{
  "agent_id": "elena",
  "voice_name": "en-US-Ava:DragonHDLatestNeural",
  "model": "gpt-realtime",
  "endpoint_configured": true
}
```

#### Voice Status

```bash
GET /api/v1/voice/status
```

**Response:**

```json
{
  "voicelive_configured": true,
  "endpoint": "https://zimax.services.ai.azure.com...",
  "model": "gpt-realtime",
  "active_sessions": 0,
  "agents": {
    "elena": {"voice": "en-US-Ava:DragonHDLatestNeural"},
    "marcus": {"voice": "en-US-GuyNeural"}
  }
}
```

#### VoiceLive WebSocket (Real-time Audio)

```javascript
// Connect to VoiceLive
const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/session-123');

ws.onopen = () => {
  // Set agent
  ws.send(JSON.stringify({ type: 'agent', agent_id: 'elena' }));
};

// Send audio (PCM16, 24kHz, mono)
function sendAudio(pcm16Base64) {
  ws.send(JSON.stringify({
    type: 'audio',
    data: pcm16Base64
  }));
}

// Switch agent mid-conversation
function switchAgent(agentId) {
  ws.send(JSON.stringify({
    type: 'agent',
    agent_id: agentId  // 'elena' or 'marcus'
  }));
}

// Cancel current response
function cancelResponse() {
  ws.send(JSON.stringify({ type: 'cancel' }));
}

// Handle responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'transcription':
      // data.status: 'listening' | 'processing' | 'complete'
      // data.text: transcribed text (when complete)
      break;
    case 'audio':
      // data.data: base64 audio response
      // data.format: 'audio/pcm16'
      playAudio(data.data);
      break;
    case 'agent_switched':
      // data.agent_id: new active agent
      break;
    case 'error':
      // data.message: error description
      break;
  }
};
```

### Audio Format Requirements

| Property | Value |
|----------|-------|
| Format | PCM16 (signed 16-bit) |
| Sample Rate | 24,000 Hz (Required for low-latency) |
| Channels | Mono (1 channel) |
| Encoding | Base64 |
| Chunk Size | 1200 samples (50ms) |

### Memory Enrichment (New)

The Voice system automatically enriches the session with user context at the start of the call:

1. **Session Start**: Upon connection, the system retrieves up to **20 relevant facts** from the user's Zep memory graph.
2. **Injection**: These facts are injected into the Agent's system instructions.
3. **Personalization**: The agent starts the conversation with awareness of the user's valid context (e.g., role, current projects).

*Note: Enrichment happens only at session start. Context learned during the call is persisted but not immediately chemically available until the next session.*

### Voice Personalities

| Agent | Voice | Personality |
|-------|-------|-------------|
| **Elena** | en-US-Ava:DragonHDLatestNeural | Warm, measured, professional |
| **Marcus** | en-US-GuyNeural | Confident, energetic, direct |

---

## Frontend Integration

### VoiceChat Component

The frontend includes a ready-to-use `VoiceChat` component:

```tsx
import VoiceChat from './components/VoiceChat';

function App() {
  return (
    <VoiceChat
      agentId="elena"
      onMessage={(msg) => console.log('Voice message:', msg)}
      onVisemes={(visemes) => /* Lip-sync data */}
      onStatusChange={(status) => console.log('Status:', status)}
    />
  );
}
```

### Push-to-Talk Usage

1. **Hold** the voice button to speak
2. **Release** to send audio
3. Agent responds with synthesized speech
4. Switch agents anytime during conversation

---

## Local Development

### Start Backend

```bash
cd backend

# Set environment variables (or use .env file)
export AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
export AZURE_AI_KEY=<your-key>
export AZURE_AI_DEPLOYMENT=gpt-5.1-chat
export AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
export AZURE_VOICELIVE_KEY=<your-key>
export AZURE_VOICELIVE_MODEL=gpt-realtime

# Start server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload
```

### Start Frontend

```bash
cd frontend
export VITE_API_URL=http://localhost:8082
export VITE_WS_URL=ws://localhost:8082
npm run dev
```

### Test Chat

```bash
curl -X POST http://localhost:8082/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello Elena!", "agent_id": "elena"}'
```

### Test Voice Status

```bash
curl http://localhost:8082/api/v1/voice/status
```

---

## Troubleshooting

### Chat Issues

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check `AZURE_AI_KEY` is set correctly |
| Model not found | Verify `AZURE_AI_DEPLOYMENT=gpt-5.1-chat` |
| Temperature error | The gateway may not support custom temperature |

### Voice Issues

| Issue | Solution |
|-------|----------|
| "VoiceLive not configured" | Set `AZURE_VOICELIVE_ENDPOINT` and `AZURE_VOICELIVE_KEY` |
| Connection failed | Verify the endpoint supports real-time audio |
| No audio response | Check microphone permissions in browser |

### WebSocket Connection

```javascript
// Debug WebSocket connection
ws.onerror = (error) => console.error('WebSocket error:', error);
ws.onclose = (event) => console.log('WebSocket closed:', event.code, event.reason);
```

---

## Related Documentation

- [Architecture](/architecture) - Platform design and context schema
- [Agents](/agents) - Elena and Marcus agent details
- [Local Testing Guide](/LOCAL-TESTING-GUIDE) - Development setup
