# VoiceLive Direct Video Routing

## Architecture Change

**Previous**: All traffic (audio, video, transcripts) flowed through backend WebSocket proxy.

**New**: Hybrid architecture:
- **Video**: Direct browser ↔ Azure (bypasses backend)
- **Audio**: Backend proxy (for memory persistence)
- **Transcripts**: Backend proxy (for memory persistence)

## Implementation

### Backend Changes

1. **Removed VIDEO modality from backend connection**:
   - Backend connection now only includes `[TEXT, AUDIO]`
   - Video is not handled by backend at all

2. **Video connection token generation**:
   - When avatar is enabled, backend generates a separate token for video-only connection
   - Token includes `modalities: ["video", "text"]` for video + video transcripts
   - Token is sent to browser in `agent_switched` message

3. **TokenRequest updated**:
   - Added `modalities` parameter (optional, defaults to `["audio", "text"]`)
   - Can be set to `["video", "text"]` for video-only connections

4. **get_realtime_token endpoint**:
   - Now supports both audio-only and video-only connections
   - Adds avatar configuration when `modalities` includes `"video"` and `agent_id == "elena"`

### Frontend Changes (TODO)

The frontend needs to be updated to:

1. **Receive video connection info**:
   - Listen for `video_connection` in `agent_switched` message
   - Extract `token`, `endpoint`, and `modalities`

2. **Establish direct video connection**:
   - Use Azure Realtime API SDK in browser
   - Connect directly to Azure using the provided token
   - Handle video events (`RESPONSE_VIDEO_DELTA`, `RESPONSE_VIDEO_DONE`)

3. **Maintain dual connections**:
   - Keep existing WebSocket for audio/transcripts (backend proxy)
   - Add new WebRTC/WebSocket connection for video (direct to Azure)

## Benefits

1. **Reduced Backend Load**: Video chunks no longer flow through backend
2. **Lower Latency**: Direct browser-to-Azure connection for video
3. **Bandwidth Savings**: Backend doesn't need to handle large video streams
4. **Memory Persistence**: Audio/transcripts still go through backend for Zep persistence

## Protocol

### Backend WebSocket (Audio/Transcripts)

**Server → Client**:
```json
{
  "type": "agent_switched",
  "agent_id": "elena",
  "video_connection": {
    "token": "ephemeral-token-here",
    "endpoint": "wss://...",
    "modalities": ["video", "text"]
  }
}
```

### Direct Video Connection (Browser ↔ Azure)

Browser establishes separate connection using:
- Token from `video_connection.token`
- Endpoint from `video_connection.endpoint`
- Modalities: `["video", "text"]`

## Next Steps

1. **Frontend Implementation**:
   - Add Azure Realtime API SDK to frontend
   - Implement direct video connection handler
   - Update `VoiceChat` component to handle dual connections

2. **Testing**:
   - Verify video works with direct connection
   - Verify audio/transcripts still work through backend
   - Verify memory persistence still works

3. **Error Handling**:
   - Handle video connection failures gracefully
   - Fallback to audio-only if video connection fails
   - Log video connection errors separately

