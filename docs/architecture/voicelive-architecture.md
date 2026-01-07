# VoiceLive Architecture

## Current Architecture (WebSocket Proxy)

### Overview
All VoiceLive traffic (audio, video, transcripts) flows through the Engram backend via WebSocket proxy. This allows the backend to:
- Persist transcripts to memory
- Apply authentication and authorization
- Monitor and log interactions
- Handle agent switching

### Data Flow

```
┌─────────┐         ┌──────────┐         ┌─────────────┐
│ Browser │ ◄─────► │  Backend │ ◄─────► │  VoiceLive  │
│         │ WebSocket│  Proxy   │  SDK   │   (Azure)   │
└─────────┘         └──────────┘         └─────────────┐
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │  Zep Memory  │
                                              │  (PostgreSQL)│
                                              └──────────────┘
```

### Video Routing

**Current Implementation: Video flows through backend**

1. **Video Generation**: VoiceLive generates avatar video in Azure
2. **Video Events**: Backend receives video events from VoiceLive SDK:
   - `RESPONSE_VIDEO_DELTA`: Streaming video chunks
   - `RESPONSE_VIDEO_DONE`: Final video URL
3. **Backend Processing**: 
   - Base64 encodes video chunks
   - Forwards to browser via WebSocket: `{"type": "avatar_video", "data": "...", "format": "video/mp4"}`
   - Forwards video URL: `{"type": "avatar_video_url", "url": "..."}`
4. **Browser Display**: Frontend receives video and displays in avatar component

**Code Location**: `backend/api/routers/voice.py` lines 540-575

### Audio Routing

**Current Implementation: Audio flows through backend**

1. **Audio Streaming**: VoiceLive streams audio chunks
2. **Backend Processing**: Receives `RESPONSE_AUDIO_DELTA` events, base64 encodes
3. **Browser Playback**: Forwards to browser via WebSocket: `{"type": "audio", "data": "...", "format": "audio/pcm16"}`

**Code Location**: `backend/api/routers/voice.py` lines 532-538

### Transcript Routing & Memory Persistence

**Current Implementation: Transcripts flow through backend to memory**

1. **User Transcripts**:
   - VoiceLive generates: `CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED`
   - Backend receives event, extracts transcript
   - Adds to `voice_context.episodic` as `Turn(role=USER, content=...)`
   - Forwards to browser for UI display
   - Persists to Zep memory in background task

2. **Assistant Transcripts**:
   - VoiceLive generates: `RESPONSE_TEXT_DELTA`, `RESPONSE_TEXT_DONE`, or `RESPONSE_AUDIO_TRANSCRIPT_DONE`
   - Backend receives events, extracts transcript
   - Adds to `voice_context.episodic` as `Turn(role=ASSISTANT, content=...)`
   - Forwards to browser for UI display
   - Persists to Zep memory in background task

3. **Memory Persistence**:
   - Background task calls `persist_conversation(voice_context)`
   - Saves to Zep with session metadata (user_id, agent_id, project_id)
   - Timeout: 10 seconds (non-blocking)

**Code Location**: 
- Transcript handling: `backend/api/routers/voice.py` lines 480-700
- Memory persistence: `backend/api/routers/voice.py` lines 450-464

### WebSocket Protocol

**Client → Server**:
- `{"type": "audio", "data": "<base64 PCM16>"}` - Audio from microphone
- `{"type": "agent", "agent_id": "elena|marcus"}` - Switch agent
- `{"type": "cancel"}` - Cancel current response

**Server → Client**:
- `{"type": "transcription", "speaker": "user|assistant", "status": "listening|processing|complete", "text": "..."}`
- `{"type": "audio", "data": "<base64>", "format": "audio/pcm16"}`
- `{"type": "avatar_video", "data": "<base64>", "format": "video/mp4"}` - Video chunk
- `{"type": "avatar_video_url", "url": "..."}` - Final video URL
- `{"type": "agent_switched", "agent_id": "..."}`
- `{"type": "error", "message": "..."}`

## Future Architecture: Direct Browser-to-Azure (WebRTC)

### `/realtime/token` Endpoint

There is a `/realtime/token` endpoint that generates ephemeral tokens for direct browser-to-Azure WebRTC connections. This would enable:

- **Direct Audio/Video**: Browser ↔ Azure (bypassing backend)
- **Lower Latency**: No backend proxy overhead
- **Backend Role**: Only handles transcripts and memory persistence

**Status**: Endpoint exists but not fully implemented in frontend

**Code Location**: `backend/api/routers/voice.py` lines 864-1029

### Hybrid Approach (Recommended)

For optimal architecture:

1. **Audio/Video**: Direct browser ↔ Azure (WebRTC) for low latency
2. **Transcripts**: Azure → Backend → Memory (for persistence)
3. **Control**: Browser ↔ Backend (agent switching, configuration)

This would require:
- Implementing WebRTC client in frontend
- Setting up transcript webhook/callback from Azure to backend
- Maintaining WebSocket for control messages

## Current Limitations

1. **Video Bandwidth**: All video chunks flow through backend, increasing bandwidth usage
2. **Latency**: Extra hop through backend adds latency to audio/video
3. **Backend Load**: Backend must handle all audio/video streaming

## Benefits of Current Architecture

1. **Memory Integration**: Backend can easily persist transcripts
2. **Security**: All traffic authenticated and authorized
3. **Observability**: Full visibility into all interactions
4. **Agent Switching**: Backend manages agent state and switching
5. **Error Handling**: Centralized error handling and logging

## Recommendations

1. **Short-term**: Keep current architecture, optimize video chunk handling
2. **Medium-term**: Implement direct WebRTC for audio/video, keep transcripts via backend
3. **Long-term**: Full WebRTC with transcript callbacks for optimal performance

