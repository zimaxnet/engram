# VoiceLive Configuration & Troubleshooting SOP

> **Last Updated**: December 21, 2025  
> **Status**: Production-Ready  
> **Maintainer**: Engram Platform Team

## Overview

VoiceLive enables real-time voice conversations with Engram agents (Elena, Marcus, Sage) using Azure's GPT Realtime API. This document captures three weeks of debugging and configuration work to establish a reliable, production-ready voice pipeline.

## Architecture

```
┌─────────────┐    WebSocket    ┌──────────────┐    WebSocket    ┌─────────────────────────┐
│   Browser   │ ◀──────────────▶│   Backend    │ ◀──────────────▶│ Azure Cognitive Services│
│  (VoiceChat)│   Audio/JSON    │ (voice.py)   │   Audio/Events  │   (gpt-realtime model)  │
└─────────────┘                 └──────────────┘                 └─────────────────────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │     Zep      │
                                │   (Memory)   │
                                └──────────────┘
```

## Prerequisites

### Azure Resources Required

| Resource | Purpose | Required Configuration |
|----------|---------|------------------------|
| Azure Cognitive Services | Hosts `gpt-realtime` model | East US 2 (or supported region) |
| Azure Key Vault | Stores API keys securely | Secret: `voicelive-api-key` |
| Azure Container Apps | Runs backend with voice router | Environment variable injection |

### Required Model Deployment

The `gpt-realtime` model must be deployed in your Azure Cognitive Services resource:

```bash
# Verify model exists
az cognitiveservices account deployment list \
  --name zimax \
  --resource-group zimax-ai \
  --query "[?name=='gpt-realtime']"
```

> [!IMPORTANT]
> The `gpt-realtime` model has **limited regional availability**. As of December 2025, it is available in:
>
> - East US 2
> - Sweden Central
> - West US 3
>
> If your resource is in an unsupported region, you must create a new Cognitive Services resource in a supported region.

## Configuration

### 1. Environment Variables

The backend requires these environment variables for VoiceLive:

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `AZURE_VOICELIVE_ENDPOINT` | Direct Cognitive Services endpoint | `https://zimax.services.ai.azure.com/` |
| `AZURE_VOICELIVE_KEY` | Cognitive Services API key | (from Key Vault) |
| `AZURE_VOICELIVE_MODEL` | Model deployment name | `gpt-realtime` |

### 2. Key Vault Configuration

```bash
# Store the VoiceLive API key in Key Vault
az keyvault secret set \
  --vault-name <your-keyvault> \
  --name voicelive-api-key \
  --value "<cognitive-services-key>"

# Retrieve the key (for verification)
az cognitiveservices account keys list \
  --name zimax \
  --resource-group zimax-ai \
  --query "key1" -o tsv
```

### 3. Infrastructure (Bicep)

The `backend-aca.bicep` file must inject the key from Key Vault:

```bicep
// In secrets array
{
  name: 'voicelive-api-key'
  keyVaultUrl: '${keyVaultUri}secrets/voicelive-api-key'
  identity: identityResourceId
}

// In environment array
{
  name: 'AZURE_VOICELIVE_KEY'
  secretRef: 'voicelive-api-key'
}
{
  name: 'AZURE_VOICELIVE_ENDPOINT'
  value: 'https://zimax.services.ai.azure.com/'
}
{
  name: 'AZURE_VOICELIVE_MODEL'
  value: 'gpt-realtime'
}
```

## Authentication Methods

### Method 1: API Key (Recommended for Production)

Use the Cognitive Services API key directly. This bypasses Managed Identity issues.

```python
from azure.core.credentials import AzureKeyCredential

credential = AzureKeyCredential(os.environ["AZURE_VOICELIVE_KEY"])
```

### Method 2: Managed Identity (Enterprise)

Use DefaultAzureCredential for Managed Identity. Requires RBAC role assignment.

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
```

> [!WARNING]
> Managed Identity authentication can hang indefinitely if RBAC is misconfigured. Always implement a connection timeout (see Troubleshooting).

## Troubleshooting

### Issue: Connection Hang (No Response)

**Symptom**: Backend hangs indefinitely when connecting to VoiceLive.

**Root Cause**: Managed Identity authentication failing silently, or model not deployed.

**Solution**:

1. Implement connection timeout:

```python
voicelive_connection = await asyncio.wait_for(
    connect(
        endpoint=endpoint,
        credential=credential,
        model=model,
    ),
    timeout=10.0
)
```

2. Switch to API Key authentication (stored in Key Vault).

### Issue: 404 Model Not Found

**Symptom**: `curl` returns 404 when testing the endpoint.

**Root Cause**: Wrong endpoint or model not deployed.

**Verification**:

```bash
# Test with correct endpoint and key
curl -X POST "https://zimax.services.ai.azure.com/openai/realtime?api-version=2024-10-01" \
  -H "api-key: <your-key>" \
  -H "Content-Type: application/json" \
  -d '{}' -v
```

### Issue: 401 Unauthorized

**Symptom**: Connection fails with 401 error.

**Root Cause**: Wrong API key or missing RBAC permissions.

**Solution**:

1. Verify you're using the Cognitive Services key (not APIM key):

```bash
az cognitiveservices account keys list \
  --name zimax \
  --resource-group zimax-ai
```

2. For Managed Identity, assign the "Cognitive Services OpenAI User" role.

### Issue: WebSocket 401 in Browser

**Symptom**: Frontend WebSocket connection fails with 401.

**Root Cause**: Azure Container Apps Platform Authentication blocking WebSockets.

**Solution**: Disable platform authentication in `backend-aca.bicep`:

```bicep
configuration: {
  activeRevisionsMode: 'Single'
  ingress: {
    // ... other config ...
  }
  // Do NOT include authConfigs that enable platform auth
}
```

## Verification Procedures

### 1. Verify VoiceLive Status (Production)

```bash
curl -s https://engram.work/api/v1/voice/status | jq '.'
```

Expected output:

```json
{
  "voicelive_configured": true,
  "endpoint": "https://zimax.services.ai.azure.com...",
  "model": "gpt-realtime",
  "active_sessions": 0,
  "agents": {
    "elena": { "voice": "en-US-Ava:DragonHDLatestNeural" },
    "marcus": { "voice": "en-US-GuyNeural" }
  }
}
```

### 2. Verify Connection (Local)

Use the verification script:

```bash
AZURE_VOICELIVE_ENDPOINT="https://zimax.services.ai.azure.com/" \
AZURE_VOICELIVE_MODEL="gpt-realtime" \
AZURE_VOICELIVE_API_KEY="<key>" \
python verify_user_no_audio.py
```

Expected output:

```
Connecting to: https://zimax.services.ai.azure.com/ Model: gpt-realtime
Using API Key
Successfully Connected!
```

### 3. Verify Audio Sample Rate

VoiceLive requires **24kHz PCM16** audio:

- **Input**: Browser captures at 48kHz, downsampled to 24kHz
- **Output**: VoiceLive sends 24kHz, frontend upsamples to 48kHz for playback

## Agent Voice Configuration

| Agent | Voice | Description |
|-------|-------|-------------|
| Elena | `en-US-Ava:DragonHDLatestNeural` | Warm, expressive female voice |
| Marcus | `en-US-GuyNeural` | Clear, professional male voice |
| Sage | (inherits Elena) | Narrative storytelling voice |

## Code References

| File | Purpose |
|------|---------|
| `backend/voice/voicelive_service.py` | VoiceLive client configuration |
| `backend/api/routers/voice.py` | WebSocket endpoint and event handling |
| `frontend/src/components/VoiceChat/` | Browser audio capture and playback |
| `infra/modules/backend-aca.bicep` | Infrastructure configuration |

## Future Architecture: VoiceLive v2 (Decoupled)

> [!NOTE]
> This section documents the **planned evolution** of VoiceLive. The current v1 implementation remains the production path until v2 is fully implemented.

### The Challenge

The current architecture routes all audio through the backend, creating:

- **Connection complexity**: The `azure-ai-voicelive` SDK's async context manager is difficult to timeout reliably
- **Latency**: Audio proxying adds round-trip delay
- **Tight coupling**: Memory enrichment and audio streaming are intertwined

### VoiceLive v2 Design

**Principle**: Separate real-time audio (latency-critical) from memory enrichment (eventually consistent).

```
┌─────────────────────────────── REALTIME PATH ───────────────────────────────┐
│  Browser ◀───── WebRTC/WebSocket ─────▶ Azure Cognitive Services (Direct)  │
│            (Audio + Transcription)           (gpt-realtime model)           │
└─────────────────────────────────────────────────────────────────────────────┘
                │
                │ Transcript text (async, fire-and-forget)
                ▼
┌─────────────────────────────── ENRICHMENT PATH ─────────────────────────────┐
│  Browser ───── POST /memory/enrich ─────▶ Backend ─────▶ Zep (Memory)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Benefits

| Aspect | v1 (Current) | v2 (Planned) |
|--------|--------------|--------------|
| Audio latency | Backend proxy | Direct browser↔Azure |
| Connection reliability | SDK hang issues | Browser handles connection |
| Memory persistence | Blocking | Async fire-and-forget |
| Failure isolation | All-or-nothing | Audio works even if memory fails |

### Implementation Path

1. **Phase 1** (Documentation): Document approach, get alignment ✅
2. **Phase 2**: Frontend direct Azure connection + backend token endpoint
3. **Phase 3**: Deprecate `/api/v1/voice/voicelive/{session_id}` endpoint

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Documented VoiceLive v2 decoupled architecture approach |
| 2025-12-21 | Fixed connection hang by adding 10s timeout |
| 2025-12-21 | Switched to API Key auth (bypassing Managed Identity issues) |
| 2025-12-21 | Stored key in Key Vault as `voicelive-api-key` |
| 2025-12-21 | Documented APIM vs Direct endpoint differences |
