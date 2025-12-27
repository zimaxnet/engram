# Voice Transcription Configuration & Troubleshooting SOP

> **Last Updated**: December 21, 2025  
> **Status**: Production-Ready  
> **Maintainer**: Engram Platform Team

## Overview

Engram provides two transcription capabilities:

1. **Live Transcription** (VoiceLive): Real-time speech-to-text during voice conversations
2. **Dictation** (Chat): One-shot audio transcription for text input

Both use Azure Cognitive Services but with different flows and purposes.

## Architecture

### Live Transcription (VoiceLive)

```
┌─────────────┐    24kHz PCM16    ┌──────────────┐    Events    ┌─────────────────────────┐
│   Browser   │ ─────────────────▶│   Backend    │ ◀───────────▶│      gpt-realtime       │
│  Microphone │                   │ (voice.py)   │              │ (transcription events)  │
└─────────────┘                   └──────┬───────┘              └─────────────────────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │   Frontend   │
                                  │ (transcript) │
                                  └──────────────┘
```

Events used:

- `CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_DELTA` - Partial user speech
- `CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED` - Final user speech
- `RESPONSE_AUDIO_TRANSCRIPT_DELTA` - Partial assistant speech
- `RESPONSE_AUDIO_TRANSCRIPT_DONE` - Final assistant speech

### Dictation (Chat Input)

```
┌─────────────┐    WAV/WebM    ┌──────────────┐    API Call    ┌─────────────────────────┐
│   Browser   │ ──────────────▶│   Backend    │ ──────────────▶│   Azure Speech Services │
│  Recording  │                │ (chat.py)    │                │   (whisper or speech)   │
└─────────────┘                └──────────────┘                └─────────────────────────┘
```

## Prerequisites

### For VoiceLive Transcription

Same as VoiceLive SOP - requires:

- `AZURE_VOICELIVE_ENDPOINT`
- `AZURE_VOICELIVE_KEY`
- `AZURE_VOICELIVE_MODEL` (gpt-realtime)

### For Dictation

Requires Azure Speech Services or OpenAI Whisper:

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_SPEECH_KEY` | Azure Speech Services key | (from Key Vault) |
| `AZURE_SPEECH_REGION` | Azure region | `eastus2` |

## Configuration

### VoiceLive Transcription

VoiceLive transcription is automatic when using the voice interface. No additional configuration needed beyond VoiceLive setup.

Transcription events are mapped to UI messages:

```python
# Backend to Frontend message mapping
{
    "type": "transcription",
    "speaker": "user" | "assistant",
    "status": "listening" | "processing" | "complete",
    "text": "transcribed text..."
}
```

### Dictation (Chat Input)

The dictation button in ChatPanel captures audio and sends it for transcription:

```typescript
// Frontend: ChatPanel.tsx
const handleDictation = async () => {
  // 1. Start recording
  // 2. Stop after silence or button press
  // 3. Send audio to /api/v1/chat/transcribe
  // 4. Insert transcribed text into input
};
```

## Audio Format Requirements

### VoiceLive (Real-time)

| Parameter | Value |
|-----------|-------|
| Format | PCM16 (raw) |
| Sample Rate | 24,000 Hz |
| Channels | Mono |
| Bit Depth | 16-bit |

> [!IMPORTANT]
> The browser records at 48kHz. The frontend **must** downsample to 24kHz before sending to the backend. The backend expects 24kHz PCM16.

### Dictation (Batch)

| Parameter | Value |
|-----------|-------|
| Format | WAV or WebM |
| Sample Rate | 16,000 Hz (optimal) |
| Channels | Mono |
| Max Duration | 60 seconds |

## Troubleshooting

### Issue: No Transcription Appearing

**Symptom**: User speaks but no text appears in the transcript area.

**Possible Causes**:

1. Microphone not accessible
2. Audio not being sent to backend
3. VoiceLive not processing audio

**Solution**:

1. Check browser microphone permissions
2. Verify WebSocket connection is established
3. Check backend logs for transcription events:

```bash
az containerapp logs show --name engram-api --resource-group engram --tail 100 | grep -i transcript
```

### Issue: Partial Transcription Only

**Symptom**: Only partial text appears, never finalizes.

**Root Cause**: `TRANSCRIPTION_COMPLETED` event not being received.

**Solution**:

1. Check VoiceLive voice activity detection (VAD) settings
2. Adjust silence threshold in backend:

```python
turn_detection=ServerVad(
    threshold=0.6,      # Lower = more sensitive
    prefix_padding_ms=300,
    silence_duration_ms=800,  # Longer = waits more before finalizing
)
```

### Issue: Wrong Sample Rate Error

**Symptom**: Audio sounds distorted or connection fails.

**Root Cause**: Frontend sending 48kHz audio instead of 24kHz.

**Solution**:
Verify frontend downsampling in VoiceChat.tsx:

```typescript
// Must downsample from 48kHz to 24kHz
const downsampledData = downsample(audioData, 48000, 24000);
```

### Issue: Dictation Button Not Working

**Symptom**: Clicking microphone button in chat does nothing.

**Root Cause**: Event handler not bound correctly.

**Solution**:

1. Check browser console for errors
2. Verify transcription API endpoint exists
3. Check CORS configuration

## Verification Procedures

### 1. Verify VoiceLive Transcription

```bash
# Check voice status
curl -s https://engram.work/api/v1/voice/status | jq '.voicelive_configured'
# Should return: true
```

### 2. Test Transcription Events (Local)

Run the backend with debug logging:

```bash
LOG_LEVEL=DEBUG python -m uvicorn backend.api.main:app
```

Look for transcription events in logs:

```
VoiceLive Event: CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_DELTA
VoiceLive Event: CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED
```

### 3. Verify Dictation Endpoint

```bash
# Test transcription endpoint (with valid audio file)
curl -X POST https://engram.work/api/v1/chat/transcribe \
  -H "Content-Type: audio/wav" \
  --data-binary @test.wav
```

## Memory Integration

Transcriptions are automatically stored in Zep memory:

```python
# User speech → memory
voice_context.episodic.add_turn(
    Turn(
        role=MessageRole.USER,
        content=final_text,
        agent_id=None,
    )
)

# Assistant speech → memory
voice_context.episodic.add_turn(
    Turn(
        role=MessageRole.ASSISTANT,
        content=final_text,
        agent_id=session.get("agent_id", "elena"),
    )
)
```

## Code References

| File | Purpose |
|------|---------|
| `backend/api/routers/voice.py` | VoiceLive transcription handling |
| `backend/api/routers/chat.py` | Dictation endpoint |
| `frontend/src/components/VoiceChat/VoiceChat.tsx` | Voice UI and audio processing |
| `frontend/src/components/ChatPanel/ChatPanel.tsx` | Dictation button handler |

## Changelog

| Date | Change |
|------|--------|
| 2025-12-21 | Initial SOP created |
| 2025-12-21 | Documented 24kHz sample rate requirement |
| 2025-12-21 | Added memory integration section |
