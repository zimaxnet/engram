---
layout: default
title: VoiceLive Avatar Integration
parent: Architecture
nav_order: 17
---

# VoiceLive Avatar Integration

> **Status**: ⚠️ Not Currently Integrated  
> **Date**: January 2026  
> **Feature**: Real-time Voice + Avatar Video Synchronization

---

## Current State

### VoiceLive (Real-time Voice)
- ✅ **Working**: Real-time voice conversations via Azure GPT Realtime API
- ✅ **Location**: `backend/api/routers/voice.py`
- ✅ **Features**: Real-time audio streaming, VAD, turn-taking
- ❌ **Avatar**: Not currently configured

### Elena's Avatar (Foundry)
- ✅ **Working**: Photorealistic video avatar via Foundry responses API
- ✅ **Location**: `backend/agents/foundry_elena_wrapper.py`
- ✅ **Features**: Video generation, natural expressions, lip-sync
- ❌ **Real-time**: Uses responses API (not real-time voice)

---

## Integration Challenge

**Current Architecture**:
```
VoiceLive (GPT Realtime API)  ←→  Real-time Audio
Foundry Responses API          ←→  Avatar Video (async)
```

**Problem**: These are separate systems:
1. **VoiceLive** uses Azure GPT Realtime API for real-time voice
2. **Elena's Avatar** uses Foundry responses API for video generation
3. They don't automatically synchronize

---

## Integration Options

### Option 1: VoiceLive Native Avatar Support ⭐ (Recommended)

Azure VoiceLive API may support avatar configuration in session settings.

**Implementation**:
```python
# In backend/api/routers/voice.py
session_config = RequestSession(
    modalities=[Modality.TEXT, Modality.AUDIO, Modality.VIDEO],  # Add VIDEO
    instructions=enriched_instructions,
    voice=AzureStandardVoice(name=agent_config.voice_name),
    avatar={
        "enabled": True,
        "avatar_id": "en-US-JennyNeural",  # Match Elena's voice
        "resolution": "1080p",
        "style": "professional",
    },
    # ... other config
)
```

**Pros**:
- Native synchronization (audio + video from same source)
- Real-time avatar video streaming
- Lower latency

**Cons**:
- Requires VoiceLive API support for avatar
- May need different avatar configuration than Foundry

**Status**: ⚠️ **Needs Verification** - Check if VoiceLive SDK supports avatar parameters

---

### Option 2: Hybrid Approach (VoiceLive Audio + Foundry Avatar)

Use VoiceLive for real-time audio, and separately fetch avatar videos from Foundry.

**Implementation**:
```python
# 1. VoiceLive provides real-time audio
# 2. When assistant responds, extract transcript
# 3. Call Foundry responses API with transcript to generate avatar video
# 4. Stream avatar video to frontend

# In process_voicelive_events():
elif event.type == ServerEventType.RESPONSE_TEXT_DONE:
    final_text = event.text
    
    # Generate avatar video from Foundry
    avatar_video_url = await generate_avatar_video(final_text)
    
    # Send to frontend
    await websocket.send_json({
        "type": "avatar_video",
        "url": avatar_video_url,
        "text": final_text,
    })
```

**Pros**:
- Uses existing Foundry avatar configuration
- Works with current architecture
- Can reuse avatar videos

**Cons**:
- Not real-time (video generated after audio)
- Additional API call latency
- Potential sync issues

**Status**: ✅ **Feasible** - Can be implemented with current systems

---

### Option 3: Foundry Agent with VoiceLive

Use Foundry agent runtime with VoiceLive for real-time voice.

**Implementation**:
- Configure Foundry agent to use VoiceLive for voice
- Foundry handles both avatar and voice synchronization

**Pros**:
- Unified system (Foundry manages both)
- Native synchronization

**Cons**:
- Requires Foundry agent runtime integration
- May need different architecture

**Status**: ⚠️ **Research Needed** - Check Foundry agent voice capabilities

---

## Recommended Approach

### Phase 1: Verify VoiceLive Avatar Support

1. **Check VoiceLive SDK Documentation**:
   - Does `RequestSession` support avatar parameters?
   - What avatar configuration options are available?

2. **Test Avatar Configuration**:
   ```python
   # Test if VoiceLive supports avatar
   session_config = RequestSession(
       modalities=[Modality.TEXT, Modality.AUDIO, Modality.VIDEO],
       avatar={"enabled": True, "avatar_id": "en-US-JennyNeural"},
       # ... other config
   )
   ```

### Phase 2: Implement Based on Findings

**If VoiceLive supports avatar**:
- Add avatar configuration to VoiceLive session
- Update frontend to display real-time avatar video
- Synchronize audio and video streams

**If VoiceLive doesn't support avatar**:
- Implement Option 2 (Hybrid Approach)
- Use VoiceLive for audio, Foundry for avatar video
- Add synchronization logic

---

## Frontend Integration

### Current VoiceLive Frontend

```typescript
// frontend/src/components/VoiceChat/VoiceChat.tsx
// Currently handles:
// - Real-time audio streaming
// - Transcription display
// - Viseme data (for lip-sync)
```

### Avatar Integration

```typescript
// Add avatar video support
interface VoiceMessage {
  type: 'audio' | 'transcription' | 'avatar_video';
  data?: string;  // Audio data or avatar video URL
  text?: string;  // Transcription
}

// Display avatar video when available
{avatarVideoUrl && (
  <video
    src={avatarVideoUrl}
    autoPlay
    playsInline
    className="voice-avatar-video"
  />
)}
```

---

## Testing

### Test VoiceLive Avatar Support

```python
# Test script: test_voicelive_avatar.py
from azure.ai.voicelive.models import RequestSession, Modality

# Try adding avatar to session config
try:
    session_config = RequestSession(
        modalities=[Modality.TEXT, Modality.AUDIO, Modality.VIDEO],
        avatar={"enabled": True},
        # ... other config
    )
    print("✅ VoiceLive supports avatar")
except Exception as e:
    print(f"❌ VoiceLive avatar not supported: {e}")
```

### Test Hybrid Approach

```python
# Test generating avatar video from transcript
async def test_hybrid_avatar():
    transcript = "Hello, how can I help you today?"
    
    # Call Foundry responses API
    avatar_video_url = await foundry_client.generate_avatar_video(
        text=transcript,
        agent_id="Elena",
    )
    
    print(f"Avatar video URL: {avatar_video_url}")
```

---

## Next Steps

1. **Research**: Verify VoiceLive SDK avatar support
2. **Test**: Try adding avatar to VoiceLive session configuration
3. **Implement**: Choose integration approach based on findings
4. **Integrate**: Update frontend to display avatar during voice conversations

---

## Summary

**Current Status**: VoiceLive and Elena's avatar are **separate systems** and don't currently work together.

**Integration Options**:
1. ⭐ **VoiceLive Native Avatar** (if supported)
2. ✅ **Hybrid Approach** (VoiceLive audio + Foundry avatar)
3. ⚠️ **Foundry Agent with VoiceLive** (research needed)

**Recommendation**: Start with **Option 1** (verify VoiceLive avatar support), then implement **Option 2** as fallback.

---

*Last Updated: January 2026*

