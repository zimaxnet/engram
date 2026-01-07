---
layout: default
title: Elena Avatar - Photorealistic Video
parent: Features
nav_order: 11
---

# Elena Avatar - Photorealistic Video

> **Status**: ✅ Production Ready  
> **Last Updated**: January 2026  
> **Feature**: Azure AI Foundry TTS Avatar

---

## Overview

Elena's **photorealistic video avatar** brings her to life with natural facial expressions, lip-sync, and professional presentation. The avatar is generated in real-time using Azure AI Foundry's TTS Avatar feature.

---

## Features

### 🎥 Video Avatar
- **Photorealistic**: High-quality video generation
- **Natural Expressions**: Facial expressions match speech
- **Lip-Sync**: Perfect synchronization with voice
- **Professional Style**: Business analyst presentation

### 🎨 Customization
- **Resolution**: 1080p (recommended), 720p, or 4K
- **Emotion**: Neutral (default), happy, sad, angry
- **Background**: Transparent (for overlays) or custom
- **Voice**: Matches Elena's voice (`en-US-JennyNeural`)

### 🔄 Integration
- **Chat Interface**: Avatar appears in message bubbles
- **Voice Chat**: Avatar displays during voice conversations
- **Automatic**: Generated automatically with each response
- **Fallback**: Gracefully falls back to static image if video unavailable

---

## How It Works

### Flow

```
User sends message
    ↓
Elena (Foundry Agent) processes
    ↓
Foundry generates avatar video
    ↓
Video URL returned to Engram
    ↓
Frontend displays video in chat
    ↓
User sees Elena speaking
```

### Technical Details

1. **Backend**: `FoundryElenaWrapper` calls Foundry's responses API with avatar enabled
2. **Foundry**: Generates photorealistic video using TTS Avatar
3. **Response**: Returns `avatar_video_url` in API response
4. **Frontend**: `ChatPanel` displays video element when URL is present
5. **Fallback**: Static image shown if video fails to load

---

## Configuration

### Prerequisites

1. ✅ **Foundry configured** (endpoint, project, agent ID)
2. ✅ **Elena created in Foundry** with avatar configuration
3. ✅ **Feature flag enabled**: `USE_FOUNDRY_ELENA=true`
4. ✅ **Tool endpoints configured** in Foundry

### Setup Steps

#### 1. Configure Avatar in Foundry

```bash
# Run configuration script
python3 scripts/configure_elena_avatar.py
```

**What it does**:
- Fetches current Elena agent definition
- Adds avatar configuration:
  - Avatar ID: `en-US-JennyNeural` (matches voice)
  - Style: Professional
  - Resolution: 1080p
  - Background: Transparent
- Creates new agent version with avatar enabled

#### 2. Verify Configuration

```bash
# Check agent version in Foundry
az rest --method GET \
  --uri "https://zimax.services.ai.azure.com/api/projects/zimax/agents/Elena?api-version=2025-11-15-preview" \
  --headers "Authorization=Bearer $(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)"
```

Look for `avatar` configuration in the agent definition.

#### 3. Enable Feature Flag

Set in Container App environment variables:

```bash
USE_FOUNDRY_ELENA=true
ELENA_FOUNDRY_AGENT_ID=Elena
```

---

## Usage

### In Chat Interface

The avatar automatically appears when:
- User sends a message to Elena
- Elena responds via Foundry
- Avatar video is successfully generated

**Display**:
- Avatar video appears in the message bubble
- Video auto-plays once
- Falls back to static image if video unavailable

### In Voice Chat

When using VoiceLive:
- Avatar displays in the main visual panel
- Updates in real-time during conversation
- Shows speaking animations

---

## Avatar Configuration Options

### Current Configuration

```json
{
  "avatar": {
    "avatar_id": "en-US-JennyNeural",
    "style": "professional",
    "emotion": "neutral",
    "resolution": "1080p",
    "background": "transparent"
  }
}
```

### Customization

You can customize the avatar by:

1. **Changing Resolution**:
   - `720p`: Standard quality (faster generation)
   - `1080p`: Recommended (balanced quality/speed)
   - `4K`: Premium quality (slower generation)

2. **Changing Emotion**:
   - `neutral`: Default professional
   - `happy`: Friendly and approachable
   - `sad`: Empathetic
   - `angry`: Serious/urgent

3. **Changing Background**:
   - `transparent`: For overlays (current)
   - Custom URL: Custom background image

**To customize**, edit `scripts/configure_elena_avatar.py` and run it again.

---

## Troubleshooting

### Avatar Not Showing

**Symptoms**:
- Static image appears instead of video
- No avatar video URL in API response

**Check**:
1. ✅ `USE_FOUNDRY_ELENA=true` is set
2. ✅ `ELENA_FOUNDRY_AGENT_ID` is correct
3. ✅ Elena agent has avatar configured in Foundry
4. ✅ Container App has access to Foundry secrets

**Debug**:
```bash
# Check environment variables
az containerapp exec --name <app-name> --resource-group <rg> \
  --command "env | grep FOUNDRY"

# Check logs for avatar generation
az containerapp logs show --name <app-name> --resource-group <rg> \
  --tail 100 | grep -i avatar
```

### Video Fails to Load

**Symptoms**:
- Video element shows error
- Falls back to static image

**Possible Causes**:
1. Video URL is invalid or expired
2. CORS issues with video hosting
3. Network connectivity problems

**Solution**:
- Check browser console for errors
- Verify video URL is accessible
- Check network tab for failed requests

### Avatar Not Generating

**Symptoms**:
- No `avatar_video_url` in API response
- Foundry returns response without avatar

**Check**:
1. Avatar is configured in Foundry agent definition
2. Foundry responses API is called with avatar enabled
3. Foundry has access to TTS Avatar service

**Debug**:
```bash
# Check Foundry agent definition
az rest --method GET \
  --uri "https://zimax.services.ai.azure.com/api/projects/zimax/agents/Elena?api-version=2025-11-15-preview" \
  --headers "Authorization=Bearer $(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)" \
  | jq '.versions.latest.definition.avatar'
```

---

## Technical Implementation

### Backend

**File**: `backend/agents/foundry_elena_wrapper.py`

```python
async def _run_foundry_agent_with_avatar(self, thread_id: str) -> tuple[str, Optional[str]]:
    """
    Execute Foundry agent with avatar enabled.
    Returns: (response_text, avatar_video_url)
    """
    url = f"{base_endpoint}/api/projects/{project}/applications/{agent}/protocols/openai/responses"
    
    payload = {
        "input": message_history,
        "extra_body": {
            "agent": {"name": self.foundry_agent_id, "type": "agent_reference"},
            "avatar": {
                "enabled": True,
                "resolution": "1080p",
                "emotion": "neutral"
            }
        }
    }
    
    response = await client.post(url, headers=headers, json=payload)
    data = response.json()
    
    response_text = data.get("output_text", "")
    avatar_video_url = data.get("avatar_video_url")
    
    return response_text, avatar_video_url
```

### Frontend

**File**: `frontend/src/components/ChatPanel/ChatPanel.tsx`

```typescript
{message.role === 'assistant' && (
  <div className="message-avatar">
    {message.avatarVideoUrl ? (
      <video
        src={message.avatarVideoUrl}
        autoPlay
        loop={false}
        className="avatar-video"
        onError={(e) => {
          // Fallback to image if video fails
          (e.target as HTMLVideoElement).style.display = 'none';
          const img = (e.target as HTMLVideoElement).nextElementSibling as HTMLImageElement;
          if (img) img.style.display = 'block';
        }}
      />
    ) : (
      <img src={agent.avatarUrl} alt={agent.name} />
    )}
  </div>
)}
```

---

## Best Practices

### ✅ Do
- Use 1080p resolution for best balance
- Keep background transparent for overlays
- Test avatar generation before production
- Monitor video generation latency
- Provide fallback to static image

### ❌ Don't
- Don't use 4K unless necessary (slower)
- Don't change emotion frequently (confusing)
- Don't rely on avatar for critical information
- Don't skip error handling

---

## Related Documentation

- [Foundry Integration](./foundry-integration.md)
- [Elena Avatar Configuration](../architecture/elena-avatar-configuration.md)
- [VoiceLive Avatar Integration](../architecture/voicelive-avatar-integration-complete.md)
- [Foundry Configuration Setup](../architecture/foundry-configuration-setup.md)

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [Technical Implementation](#technical-implementation)
- Check application logs: `az containerapp logs show`

