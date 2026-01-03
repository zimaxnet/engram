# VoiceLive Configuration and Reference Implementation

## Overview

This document serves as the **Reference Configuration** for the Azure VoiceLive integration. It includes the correct environment variables and a reference Python implementation for a basic voice assistant using the `azure.ai.voicelive` SDK.

## Working Configuration

These are the validated configuration values for the `zimax` environment:

```bash
AZURE_VOICELIVE_ENDPOINT="https://zimax.services.ai.azure.com/"
AZURE_VOICELIVE_AGENT_ID=""
AZURE_VOICELIVE_PROJECT_NAME="zimax"  # CRITICAL: Must be set for unified endpoints
AZURE_VOICELIVE_API_VERSION="2025-10-01"
AZURE_ENV_NAME="voice-lives-playground-7401"
AZURE_LOCATION="eastus2"
AZURE_SUBSCRIPTION_ID="23f4e2c5-0667-4514-8e2e-f02ca7880c95"
AZURE_EXISTING_AIPROJECT_ENDPOINT="https://zimax.services.ai.azure.com/api/projects/zimax"
AZURE_EXISTING_AIPROJECT_RESOURCE_ID="/subscriptions/23f4e2c5-0667-4514-8e2e-f02ca7880c95/resourceGroups/zimax-ai/providers/Microsoft.CognitiveServices/accounts/zimax/projects/zimax"
AZD_ALLOW_NON_EMPTY_FOLDER=true
```

## System Update

Based on this reference, the Engram backend has been updated to include:

- **`AZURE_VOICELIVE_PROJECT_NAME="zimax"`** in `config.py` and `backend-aca.bicep`.

## Reference Implementation

A full Python script demonstrating the use of `azure.ai.voicelive` with this configuration is saved at:
[scripts/reference/voice_live_client.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/scripts/reference/voice_live_client.py)

### Key Features of Reference Script

1. **Audio Processor:** Handles PCM16 24kHz audio capture (PyAudio) and playback in separate threads.
2. **WebSocket Connection:** Uses `azure.ai.voicelive.aio.connect` for secure, real-time communication.
3. **Session Management:** Configures modalities (Audio+Text), VAD, and Voice settings.
4. **Event Handling:** robustly handles `RESPONSE_AUDIO_DELTA`, `INPUT_AUDIO_BUFFER_SPEECH_STARTED` (barge-in), and `RESPONSE_DONE` events.

## Usage

To run the reference script locally:

```bash
# Ensure you are in the scripts/reference directory or adjust paths
cd scripts/reference

# Install dependencies (if not already installed)
pip install azure-ai-voicelive[aiohttp] pyaudio python-dotenv

# Run the script
python voice_live_client.py --api-key YOUR_KEY
```
