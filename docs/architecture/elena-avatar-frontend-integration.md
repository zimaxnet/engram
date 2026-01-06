---
layout: default
title: Elena Avatar Frontend Integration
parent: Architecture
nav_order: 16
---

# Elena Avatar Frontend Integration ✅

> **Status**: ✅ Integration Complete  
> **Date**: January 2026  
> **Feature**: Foundry Avatar Video Display in Engram Website

---

## Overview

Elena's Foundry avatar is now integrated into the Engram website. When users interact with Elena, they see her photorealistic video avatar speaking with natural voice and expressions.

---

## Implementation

### Backend Changes

1. **FoundryElenaWrapper** (`backend/agents/foundry_elena_wrapper.py`)
   - Updated `run()` method to return `(response_text, context, avatar_video_url)`
   - Added `_run_foundry_agent_with_avatar()` method
   - Uses Foundry's responses API with avatar enabled
   - Extracts `avatar_video_url` from response

2. **Agent Router** (`backend/agents/router.py`)
   - Updated `route_and_execute()` to return `(response, context, agent_id, avatar_video_url)`
   - Handles Foundry Elena wrapper's avatar video URL

3. **Chat Router** (`backend/api/routers/chat.py`)
   - Updated `ChatResponse` model to include `avatar_video_url`
   - Extracts avatar video URL from agent response
   - Returns avatar video URL in API response

### Frontend Changes

1. **Message Interface** (`frontend/src/components/ChatPanel/ChatPanel.tsx`)
   - Added `avatarVideoUrl?: string` to `Message` interface
   - Extracts `avatar_video_url` from API response
   - Displays video in message avatar when available

2. **AvatarDisplay Component** (`frontend/src/components/AvatarDisplay/AvatarDisplay.tsx`)
   - Added `avatarVideoUrl?: string` prop
   - Shows video when available, falls back to static image
   - Maintains existing animation and viseme support

3. **ChatPanel Component** (`frontend/src/components/ChatPanel/ChatPanel.tsx`)
   - Updated message avatar to show video when `avatarVideoUrl` is present
   - Falls back to static image if video fails or not available
   - Maintains circular avatar styling

4. **CSS Updates**
   - Added styles for `.avatar-video` in both `ChatPanel.css` and `AvatarDisplay.css`
   - Maintains circular shape and proper sizing

---

## How It Works

### Flow

```
User sends message
    ↓
Backend: FoundryElenaWrapper.run()
    ↓
Foundry Responses API (with avatar enabled)
    ↓
Foundry generates avatar video
    ↓
Backend extracts avatar_video_url from response
    ↓
API returns ChatResponse with avatar_video_url
    ↓
Frontend receives response
    ↓
ChatPanel displays video in message avatar
    ↓
User sees Elena's avatar video speaking
```

### Avatar Video Display

**In Chat Messages**:
- When Elena responds, if `avatar_video_url` is present, a `<video>` element is shown
- Video auto-plays, loops once, and is muted by default
- Falls back to static image if video fails to load

**In AvatarDisplay Component**:
- Can receive `avatarVideoUrl` prop
- Shows video when available
- Maintains all existing animations and viseme support

---

## Configuration

### Backend

The avatar is automatically enabled when:
- `USE_FOUNDRY_ELENA=true`
- `ELENA_FOUNDRY_AGENT_ID` is set
- Elena agent has avatar configured in Foundry (Version 3)

### Frontend

No additional configuration needed. The frontend automatically:
- Detects `avatar_video_url` in API responses
- Displays video when available
- Falls back gracefully if video is not available

---

## User Experience

### When Avatar Video is Available

1. **User sends message** to Elena
2. **Elena responds** with text and avatar video URL
3. **Avatar video displays** in the message avatar
4. **Video plays** showing Elena speaking
5. **Natural experience** with photorealistic avatar

### When Avatar Video is Not Available

1. **User sends message** to Elena
2. **Elena responds** with text only
3. **Static avatar image** displays (existing behavior)
4. **No degradation** in user experience

---

## Testing

### Test Avatar Display

1. **Enable Foundry Elena**:
   ```bash
   export USE_FOUNDRY_ELENA=true
   export ELENA_FOUNDRY_AGENT_ID=Elena
   ```

2. **Send a message** to Elena in the Engram website

3. **Verify**:
   - Avatar video displays in message
   - Video plays automatically
   - Falls back to image if video fails

### Verify Avatar Video URL

Check the API response:
```bash
curl -X POST "https://engram.work/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello Elena!",
    "agent_id": "elena"
  }'
```

Response should include:
```json
{
  "content": "...",
  "avatar_video_url": "https://...",  // If available
  ...
}
```

---

## Fallback Behavior

### Video Fails to Load

1. **Frontend detects error** via `onError` handler
2. **Replaces video** with static image
3. **User sees** static avatar (no broken video)

### Avatar Not Configured

1. **Backend returns** response without `avatar_video_url`
2. **Frontend displays** static image (existing behavior)
3. **No errors** or broken UI

### Foundry Not Enabled

1. **Backend uses** LangGraph Elena (no avatar)
2. **Frontend displays** static image
3. **Normal operation** continues

---

## Performance Considerations

### Video Loading

- **Lazy Loading**: Videos load when message is displayed
- **Error Handling**: Graceful fallback to static image
- **Caching**: Browser caches videos for reuse

### Bandwidth

- **1080p Resolution**: Good balance of quality and size
- **Transparent Background**: Smaller file size
- **Optimization**: Consider CDN for video delivery

---

## Future Enhancements

### Potential Improvements

1. **Video Caching**: Cache avatar videos for common responses
2. **Progressive Loading**: Show static image while video loads
3. **Loading States**: Show loading indicator while video generates
4. **Video Controls**: Allow users to replay avatar videos
5. **Emotion Control**: Adjust avatar emotion based on message tone

---

## Summary

✅ **Avatar Integration Complete**
- Backend returns `avatar_video_url` from Foundry
- Frontend displays video in chat messages
- Graceful fallback to static image
- No breaking changes to existing functionality

**Elena's avatar now appears in the Engram website** when users interact with her, providing a more engaging and immersive experience.

---

*Last Updated: January 2026*

