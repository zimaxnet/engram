---
layout: default
title: Elena Avatar Configuration - Azure AI Foundry
parent: Architecture
nav_order: 15
---

# Elena Avatar Configuration - Azure AI Foundry

> **Status**: Ready for Configuration  
> **Date**: January 2026  
> **Feature**: Azure AI Foundry TTS Avatar

---

## Overview

Azure AI Foundry's TTS Avatar feature enables Elena to have a **photorealistic video avatar** that speaks with natural voice and expressions. This creates a more engaging and interactive user experience.

---

## Avatar Features

### ✅ Available Features

1. **Photorealistic Video Avatar**
   - High-quality video generation
   - Natural facial expressions
   - Lip-sync with speech

2. **Voice Integration**
   - Uses Elena's voice: `en-US-JennyNeural`
   - Natural-sounding speech
   - Emotion control

3. **Resolution Options**
   - 720p (standard)
   - 1080p (recommended)
   - 4K (premium)

4. **Emotion Control**
   - Neutral (default)
   - Happy
   - Sad
   - Angry
   - Custom emotions

5. **Background Options**
   - Transparent (for overlays)
   - Custom backgrounds

---

## Configuration

### Method 1: Script (Recommended)

Use the configuration script:

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
source .venv/bin/activate
python3 scripts/configure_elena_avatar.py
```

**What it does**:
- Fetches current Elena agent definition
- Adds avatar configuration
- Creates new agent version with avatar enabled

### Method 2: Azure Portal

1. Go to: Azure AI Foundry → Project `zimax` → Applications → `Elena`
2. Navigate to: Avatar settings
3. Configure:
   - Avatar ID: `en-US-JennyNeural` (matches Elena's voice)
   - Style: Professional
   - Resolution: 1080p
   - Background: Transparent

### Method 3: REST API

```bash
# Get access token
TOKEN=$(az account get-access-token --resource "https://ai.azure.com" --query accessToken -o tsv)

# Get current agent
curl -X GET \
  "https://zimax.services.ai.azure.com/api/projects/zimax/agents/Elena?api-version=2025-11-15-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Create new version with avatar config
curl -X POST \
  "https://zimax.services.ai.azure.com/api/projects/zimax/agents/Elena/versions?api-version=2025-11-15-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "definition": {
      "kind": "prompt",
      "instructions": "...",
      "model": "gpt-5.1-chat",
      "tools": [...],
      "avatar": {
        "avatar_id": "en-US-JennyNeural",
        "style": "professional",
        "emotion": "neutral",
        "resolution": "1080p",
        "background": "transparent"
      }
    }
  }'
```

---

## Avatar Configuration Schema

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

### Configuration Options

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `avatar_id` | string | Standard avatars or custom ID | Avatar to use (matches voice) |
| `style` | string | professional, casual, friendly | Avatar presentation style |
| `emotion` | string | neutral, happy, sad, angry | Default emotion |
| `resolution` | string | 720p, 1080p, 4K | Video resolution |
| `background` | string | transparent, custom URL | Background type |

---

## Integration with Engram

### Frontend Integration

Elena's avatar can be displayed in the frontend:

```typescript
// AvatarDisplay component already supports Elena
<AvatarDisplay
  agentId="elena"
  isSpeaking={isSpeaking}
  expression={expression}
  visemes={visemes}
  showName={true}
  size="lg"
/>
```

### Backend Integration

When Elena responds via Foundry, the avatar video is automatically generated:

```python
# Foundry agent response includes avatar video URL
response = await foundry_client.invoke_agent(
    agent_id="Elena",
    thread_id=thread_id,
    user_id=user_id,
)

# Response includes:
# - text: Response text
# - avatar_video_url: URL to generated avatar video (if enabled)
# - avatar_audio_url: URL to audio track
```

---

## Custom Avatar Creation

### Option 1: Standard Avatar

Use Azure's pre-built avatars:
- `en-US-JennyNeural` (matches Elena's voice)
- Professional appearance
- Ready to use immediately

### Option 2: Custom Avatar

Create a custom avatar with Elena's likeness:

1. **Record Training Video**:
   - Record video of talent (with consent)
   - Professional lighting and setup
   - Clear audio

2. **Upload to Foundry**:
   - Go to: Azure AI Foundry → Avatar Studio
   - Upload training video
   - Configure settings

3. **Train Avatar Model**:
   - Foundry trains the model
   - Takes several hours
   - Notifies when complete

4. **Deploy Avatar**:
   - Assign to Elena agent
   - Test and verify

**Requirements**:
- Consent from talent
- High-quality video recording
- Professional setup

---

## Usage Examples

### Generate Avatar Video

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

client = AIProjectClient(
    endpoint="https://zimax.services.ai.azure.com/api/projects/zimax",
    credential=DefaultAzureCredential(),
)

agent = client.agents.get(agent_name="Elena")
openai_client = client.get_openai_client()

# Get response with avatar
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Tell me about the GTM strategy"}],
    extra_body={
        "agent": {"name": agent.name, "type": "agent_reference"},
        "avatar": {
            "enabled": True,
            "resolution": "1080p",
            "emotion": "neutral"
        }
    },
)

# Response includes avatar video URL
avatar_video_url = response.avatar_video_url
print(f"Avatar video: {avatar_video_url}")
```

### Display Avatar in Frontend

```typescript
// When Elena responds, display avatar video
if (response.avatar_video_url) {
  setAvatarVideoUrl(response.avatar_video_url);
  setIsSpeaking(true);
}

// In component
{avatarVideoUrl && (
  <video
    src={avatarVideoUrl}
    autoPlay
    loop={false}
    className="elena-avatar-video"
  />
)}
```

---

## Cost Considerations

### Avatar Generation Costs

- **Standard Avatar**: Lower cost, pre-built
- **Custom Avatar**: Higher cost, requires training
- **Resolution**: 4K costs more than 1080p
- **Usage**: Pay per video generated

### Optimization Tips

1. **Use Standard Avatar**: Lower cost than custom
2. **1080p Resolution**: Good balance of quality and cost
3. **Cache Videos**: Reuse avatar videos for common responses
4. **Batch Generation**: Generate multiple videos at once

---

## Testing

### Test Avatar Generation

```bash
# Test avatar in Azure Portal
# Azure AI Foundry → Project 'zimax' → Applications → 'Elena' → Test

# Or use REST API
curl -X POST \
  "https://zimax.services.ai.azure.com/api/projects/zimax/applications/Elena/protocols/openai/responses?api-version=2025-11-15-preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "Hello Elena!"}],
    "extra_body": {
      "agent": {"name": "Elena", "type": "agent_reference"},
      "avatar": {"enabled": true}
    }
  }'
```

### Verify Avatar Quality

1. Check video resolution
2. Verify lip-sync accuracy
3. Test emotion expressions
4. Validate background transparency

---

## Next Steps

1. **Run Configuration Script**:
   ```bash
   python3 scripts/configure_elena_avatar.py
   ```

2. **Test Avatar**:
   - Use Azure Portal test interface
   - Verify video generation
   - Check quality and sync

3. **Integrate with Frontend**:
   - Update AvatarDisplay component
   - Add video playback
   - Handle avatar URLs

4. **Customize (Optional)**:
   - Create custom avatar
   - Adjust emotions
   - Upgrade to 4K

---

## Summary

✅ **Avatar Feature Available** in Azure AI Foundry  
✅ **Configuration Script Ready** (`scripts/configure_elena_avatar.py`)  
✅ **Integration Points Identified** (frontend and backend)  
✅ **Documentation Complete**

**Elena can now have a photorealistic video avatar** that speaks with natural voice and expressions, creating a more engaging user experience.

---

*Last Updated: January 2026*

