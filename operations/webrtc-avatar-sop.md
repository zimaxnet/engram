# Enterprise WebRTC Avatar SOP

## 1. Overview

This document outlines the standard operating procedure (SOP) for the WebRTC Avatar functionality in Engram ("Geneva" Release). This feature enables real-time, low-latency voice and video interaction with AI agents (Elena, Marcus) via Azure AI Speech and Azure OpenAI Realtime API.

## 2. Architecture

The WebRTC implementation uses a "Direct-to-Avatar" pattern to minimize latency:

1. **Frontend**: Requests an ephemeral `Realtime Token` and `ICE Credentials` from the Engram Backend.
2. **Backend**: Authenticates the user and proxies the token generation request to Azure.
3. **Frontend**: Uses the token to establish a direct WebRTC WebSocket connection to Azure (`wss://...`).

See [WebRTC Avatar Diagram](../architecture/webrtc-avatar-diagram.json) for the visual architecture.

## 3. Configuration Requirements

### Environment Variables

The following environment variables must be configured in the Azure Container App (Backend):

| Variable | Description | Required? | Example |
| :--- | :--- | :--- | :--- |
| `AZURE_VOICELIVE_ENDPOINT` | The Azure AI Services endpoint. | **Yes** | `https://zimax.services.ai.azure.com/` |
| `AZURE_VOICELIVE_KEY` | API Key for the AI Service. Optional if using Managed Identity. | Optional | `cf23...` |
| `AZURE_SPEECH_KEY` | Dedicated Speech Service key. **Critical for ICE Credentials.** | **Yes** (Ent) | `12b2...` |
| `AZURE_SPEECH_REGION` | Region for the Speech Service. | **Yes** (Ent) | `eastus2` |

### Golden Configuration (Reference)

The following values are verified to work in the `eastus2` environment:

- **Project**: `zimax`
- **Model**: `gpt-realtime`
- **API Version**: `2025-10-01`
- **Voice**: `en-US-Ava:DragonHDLatestNeural`

> [!IMPORTANT]
> **Enterprise Configuration Note**: The `/ice-credentials` endpoint often fails with a 500 error if relying solely on Managed Identity against a "Unified" Cognitive Service account. For robust Enterprise deployment, a **dedicated Azure Speech Service key** (`AZURE_SPEECH_KEY`) is recommended to ensure reliable TURN credential generation.

## 4. Authentication Flow

### 4.1. ICE Credentials (TURN)

- **Endpoint**: `POST /api/v1/voice/avatar/ice-credentials`
- **Auth**: User JWT (Bearer Token)
- **Backend Action**: Fetches TURN credentials from Azure Speech Relay service.
- **Enterprise Note**: Uses `AZURE_SPEECH_KEY` if available; falls back to `AZURE_VOICELIVE_KEY` or Managed Identity.

### 4.2. Realtime Token

- **Endpoint**: `POST /api/v1/voice/realtime/token`
- **Body**: `{"agent_id": "elena"}`
- **Auth**: User JWT (Bearer Token)
- **Backend Action**: Generates an ephemeral access token for the `gpt-realtime` model.
- **Support**: Supports both `services.ai.azure.com` (Unified) and `azure-api.net` (APIM) endpoints.

## 5. Verification Tools

### Client Verification Script

We have included a reference Python client script that mimics the WebRTC connection logic using the `azure.ai.voicelive` SDK. This is useful for isolating backend/network issues from frontend code.

**Location**: `scripts/verify_voicelive_client.py`

**Usage**:

```bash
# Set required env vars
export AZURE_VOICELIVE_ENDPOINT="https://zimax.services.ai.azure.com/"
export AZURE_VOICELIVE_API_KEY="<key>"

# Run verification
python3 scripts/verify_voicelive_client.py --verbose
```

## 6. Troubleshooting (SOP)

### Incident: 500 Internal Server Error on `/ice-credentials`

**Cause**: The backend cannot authenticate with the Azure Speech Relay service.
**Resolution**:

1. Check if `AZURE_SPEECH_KEY` is set in the container environment.
2. If using Managed Identity, ensure the identity has `Cognitive Services Speech User` role on the specific Speech resource.
3. Verify `AZURE_SPEECH_REGION` matches the resource region.

### Incident: 400/502 Bad Gateway on `/realtime/token`

**Cause**: Invalid endpoint format or networking issue.
**Resolution**:

1. Verify `AZURE_VOICELIVE_ENDPOINT` is a valid HTTPS URL.
2. If using APIM, ensure the backend allows the domain (fixed in `voice.py` update to include `azure-api.net`).

### Incident: WebSocket Connection Failed (Frontend)

**Cause**: Token expired or ICE negotiation failed.
**Resolution**:

1. Check browser console for WebRTC errors.
2. Verify the firewall allows UDP traffic on the ports returned by `/ice-credentials`.
