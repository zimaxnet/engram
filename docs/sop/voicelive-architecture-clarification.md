# VoiceLive Architecture Clarification

## Architecture Overview

The VoiceLive WebSocket proxy architecture works as follows:

```
┌─────────────────┐         WebSocket          ┌──────────────────┐         VoiceLive SDK         ┌─────────────────────┐
│   Browser       │ ◀────────────────────────▶│   Backend        │ ◀──────────────────────────▶│  Azure VoiceLive    │
│  (SWA Frontend) │   wss://backend/voicelive/ │  (Container App) │   Direct Connection        │  (gpt-realtime)     │
│                 │                             │                  │                             │                     │
│ VoiceChat.tsx   │                             │ voice.py         │                             │ Cognitive Services  │
└─────────────────┘                             └──────────────────┘                             └─────────────────────┘
       │                                                 │                                                    │
       │ Audio chunks                                    │                                                    │
       │ Transcripts                                      │ Audio + Events                                    │
       │                                                 │                                                    │
       │                                                 │ (Automatic Memory Persistence)                     │
       │                                                 ▼                                                    │
       │                                         ┌──────────────────┐                                        │
       └────────────────────────────────────────▶│   Zep Memory     │                                        │
                                                 │   (Episodic)     │                                        │
                                                 └──────────────────┘                                        │
```

## Key Points

### 1. SWA is the Frontend (Browser)

The **Static Web App (SWA)** is the frontend code that runs in the user's browser:
- **Location**: `https://engram.work` (deployed to Azure Static Web Apps)
- **Code**: React/TypeScript application (`frontend/` directory)
- **Component**: `VoiceChat.tsx` handles voice interaction
- **Connection**: Browser connects to backend via WebSocket

### 2. Backend is the Proxy

The **Backend (Container App)** acts as a WebSocket proxy:
- **Location**: `staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io`
- **Endpoint**: `/api/v1/voice/voicelive/{session_id}`
- **Function**: 
  - Receives WebSocket connection from browser
  - Connects to Azure VoiceLive using SDK
  - Proxies audio and events between browser and Azure
  - Automatically persists transcripts to Zep memory

### 3. Flow Direction

**Audio Flow**:
1. **User speaks** → Browser captures audio (microphone)
2. **Browser** → Sends audio chunks to **Backend** via WebSocket
3. **Backend** → Forwards audio to **Azure VoiceLive**
4. **Azure VoiceLive** → Processes audio, generates response
5. **Azure VoiceLive** → Sends audio + transcripts back to **Backend**
6. **Backend** → Forwards audio + transcripts to **Browser**
7. **Browser** → Plays audio and displays transcripts

**Memory Flow**:
1. **Backend** → Extracts transcripts from VoiceLive events
2. **Backend** → Stores transcripts in EnterpriseContext
3. **Backend** → Persists to **Zep Memory** (async, non-blocking)

## Why Proxy Through Backend?

### Benefits

1. **Works with Unified Endpoints**
   - Unified endpoints (`services.ai.azure.com`) don't support REST token endpoints
   - WebSocket proxy bypasses this limitation

2. **Automatic Memory Integration**
   - Backend automatically extracts transcripts
   - Persists to Zep without frontend code
   - Memory enrichment happens automatically

3. **Simplified Frontend**
   - No need to manage Azure tokens
   - No need to handle VoiceLive SDK complexity
   - Just connect to backend WebSocket

4. **Better Error Handling**
   - Backend can retry connections
   - Backend can handle reconnection logic
   - Centralized error handling

5. **Security**
   - API keys stay on backend
   - No exposure to browser
   - Backend handles authentication

## Alternative Architecture (Not Used)

### Direct Browser-to-Azure (Token Endpoint)

```
Browser → Get Token from Backend → Connect Directly to Azure
```

**Why Not Used**:
- ❌ Token endpoint doesn't work with unified endpoints
- ❌ Requires direct OpenAI endpoint (`openai.azure.com`)
- ❌ Frontend must manage tokens
- ❌ No automatic memory persistence

## Summary

**The voice does NOT proxy through the backend to get to the SWA.**

**Correct understanding**:
- **SWA** = Frontend (runs in browser)
- **Backend** = WebSocket proxy (runs in Container App)
- **Flow**: Browser (SWA) → Backend → Azure VoiceLive

The backend is a **proxy between the browser and Azure**, not between Azure and the SWA. The SWA IS the browser frontend.

## Visual Flow

```
User's Browser (SWA Frontend)
    │
    │ WebSocket: wss://backend/api/v1/voice/voicelive/{session_id}
    │
    ▼
Backend Container App (Proxy)
    │
    │ VoiceLive SDK Connection
    │
    ▼
Azure VoiceLive (gpt-realtime)
    │
    │ Transcripts (async)
    │
    ▼
Zep Memory (Episodic Storage)
```

The backend sits **between** the browser and Azure, proxying the connection and handling memory persistence automatically.

