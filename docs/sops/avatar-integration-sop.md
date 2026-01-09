# Standard Operating Procedure: Azure Avatar Integration (Engram)

**Version:** 1.0
**Last Updated:** 2026-01-08
**Owner:** Engram Platform Team
**Status:** Live (West US 2)

---

## 1. System Overview

The Engram Avatar System provides a real-time, interactive visual interface for AI agents (specifically Dr. Elena Vasquez). It leverages **Azure AI Speech Service (Text-to-Speech Avatar Check)** to stream low-latency WebRTC video synchronized with generated audio.

### 1.1 Key Capabilities

* **Real-time Animation:** Lip-sync and facial expressions generated dynamically from text.
* **WebRTC Streaming:** Sub-second latency video using direct peer-to-peer or TURN relay connections.
* **Mobile-First Design:** Full-screen overlay experience on mobile devices with touch-optimized "Hold-to-Speak" controls.
* **Fallback Resilience:** Graceful degradation to a static portrait with CSS-based animation if the video stream fails.

---

## 2. Architecture

### 2.1 Critical Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Frontend** | React (Vite) | UI/UX, WebRTC signal handling, Media rendering. |
| **Backend** | Python (FastAPI) | Auth token generation, ICE credential proxying, Signal routing. |
| **Service** | Azure AI Speech | Video generation, RTP streaming, STUN/TURN services. |
| **Identity** | Managed Identity | Secure, keyless access to Azure resources (Key Vault). |
| **Key Vault** | Azure Key Vault | Storage of `AZURE_SPEECH_KEY` (Fallback auth). |

### 2.2 Data Flow (Connection Sequence)

1. **Identity Exchange:**
    * Frontend requests ICE credentials via `GET /api/v1/voice/avatar/ice-credentials`.
    * Backend authenticates with Azure via Managed Identity (or Key Vault fallback) and returns TURN tokens.
2. **Signaling (SDP Handshake):**
    * Frontend initializes `RTCPeerConnection` and sends `offer` (SDP) to Backend via WebSocket.
    * Backend forwards offer to Azure Speech Service.
    * Azure returns `answer` (SDP), which Backend relays to Frontend.
3. **Media Transport (WebRTC):**
    * Browser establishes UDP/TCP connection to Azure TURN server (or direct P2P).
    * **Port:** 3478 (STUN/TURN).
    * **Protocol:** RTP/SRTP (Secure Real-time Transport Protocol).

---

## 3. Configuration & Environment

**Region Requirement:** `westus2` (Strict requirement for Avatar features).

### 3.1 Backend Variables (`.env`)

```bash
AZURE_SPEECH_REGION="westus2"
AZURE_VOICELIVE_ENDPOINT="wss://westus2.tts.speech.microsoft.com/cognitiveservices/avatar/to/speech/1"
AZURE_VOICELIVE_API_VERSION="2024-10-01-preview"
# Keys are loaded from Azure Key Vault automatically in prod
```

### 3.2 Frontend Components

* **`VoiceChat.tsx`**: The "Brain". Handles microphone input (`AudioContext`), WebSocket signaling, and ICE candidate exchange.
* **`AvatarDisplay.tsx`**: The "Face". Renders the `<video>` element or static fallback. Handles layering and error states.
* **`ChatPanel.tsx`**: The "Container". Manages the mobile overlay and auto-engage logic.

---

## 4. Operational Procedures

### 4.1 Deployment

* **Infrastructure:** Deployed via Azure Bicep to Azure Container Apps.
* **Scaling:** Stateless backend allows horizontal scaling (KEDA rules based on HTTP traffic).

### 4.2 Maintenance

* **Token Rotation:** Managed Identities rotate automatically. If using fallback Keys in Key Vault, rotate every 90 days.
* **Library Updates:** Monitor `azure-ai-voicelive` and `azure-identity` Python packages for security patches.

### 4.3 Monitoring

* **Logs:** Check Container App logs for "ICE connection state" and "VoiceLive" errors.
* **User Reports:** Watch for "Amber Dot" reports (indicates fallback mode).

---

## 5. Troubleshooting Guide

### 5.1 "ICE Connection Disconnected" / Amber Dot Visible

* **Symptom:** User hears audio but sees static image with amber dot.
* **Cause:** WebRTC media path blocked (Firewall/VPN blocking UDP 3478).
* **Fix:**
    1. User: Switch networks (e.g., WiFi to 5G).
    2. Admin: Ensure Enterprise firewall whitelist includes `*.speech.microsoft.com` and Azure IP ranges.
    3. Code: Confirm `iceTransportPolicy` is NOT set to `'relay'` only (Relaxed in Rev 166).

### 5.2 401 Unauthorized

* **Symptom:** Connection fails immediately. Console shows 401.
* **Cause:** Invalid Speech Key or Region Mismatch.
* **Fix:**
    1. Verify `AZURE_SPEECH_REGION` is `westus2`.
    2. Check Key Vault secret `azure-speech-key`.
    3. Restart Backend Container to reload env vars.

### 5.3 "Image Blocking Video" (Layering Glitch)

* **Symptom:** Static image stays on top of video.
* **Cause:** Race condition where dummy URL was set before stream ready (Fixed in Rev 165).
* **Fix:** Ensure Frontend is running Rev 165+.

---

## 6. Development Workflow

### 6.1 Local Testing

1. Run `npm run dev` in `frontend/`.
2. Set `.env` in `backend/` to point to `westus2` resource.
3. Access `localhost:5173`.
4. Navigate to **Chat**, tap **Mic**. Avatar should load.

### 6.2 Adding New Avatars

1. Define new Agent in `types.ts`.
2. Add portrait image to `public/assets/images/`.
3. Update `AvatarDisplay.tsx` `AGENT_INFO` map with colors and default image.
