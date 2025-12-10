# Voice Consolidation Plan

## Current State Analysis

### Voice Endpoints Found

1. **VoiceLive WebSocket** (`/api/v1/voice/voicelive/{session_id}`)
   - ✅ Primary endpoint (what we want)
   - ❌ No avatar integration
   - ❌ No viseme data sent to frontend

2. **Legacy Speech Services WebSocket** (`/api/v1/voice/ws/{session_id}`)
   - ❌ Uses separate STT/TTS pipeline
   - ✅ Has avatar integration
   - ❌ Should be removed/deprecated

3. **REST Endpoints** (Speech Services)
   - `/api/v1/voice/transcribe` - POST endpoint
   - `/api/v1/voice/synthesize` - POST endpoint
   - `/api/v1/voice/avatar/session` - Avatar session management
   - ❌ These use Speech Services, not VoiceLive

### Avatar Functionality

- Avatar service exists (`backend/voice/avatar_service.py`)
- Viseme-to-blendshape mapping available
- Avatar session management implemented
- **NOT integrated with VoiceLive**

## Required Changes

### 1. Integrate Avatar with VoiceLive

- Add avatar session creation to VoiceLive WebSocket
- Send viseme data from VoiceLive to frontend
- Integrate avatar service with VoiceLive event handlers
- Add avatar speaking notifications

### 2. Remove Legacy Endpoints

- Deprecate `/api/v1/voice/ws/{session_id}` endpoint
- Consider keeping REST endpoints for backward compatibility OR remove them
- Update documentation

### 3. Update Frontend

- Ensure frontend only uses VoiceLive endpoint
- Add avatar display component
- Handle viseme data for lip-sync

### 4. VoiceLive Event Enhancement

- Check if VoiceLive SDK provides viseme data
- If not, generate visemes from audio or text
- Send viseme events to frontend

## Implementation Steps

1. ✅ Review current code (DONE)
2. ⏳ Integrate avatar into VoiceLive WebSocket
3. ⏳ Add viseme data to VoiceLive events
4. ⏳ Remove/deprecate legacy `/ws/` endpoint
5. ⏳ Update frontend to display avatar
6. ⏳ Test end-to-end flow

