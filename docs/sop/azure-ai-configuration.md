# Azure AI Configuration & Troubleshooting SOP

## Overview

Engram uses a dual-path approach for Azure AI integration:

1. **Azure API Management (APIM)**: The primary gateway for standard LLM calls (OpenAI-compatible). This provides rate limiting, monitoring, and unified access control.
2. **Azure AI Foundry (Direct)**: Used for specialized services like "VoiceLive" (Real-time API) that require direct WebSocket connections or features not yet supported by the APIM gateway.

## Configuration Standards

### 1. Azure APIM Gateway (Primary Chat)

For standard agent chat (`gpt-5-chat`, `gpt-4o`), the backend **MUST** connect via the APIM Gateway.

* **Endpoint**: `https://zimax-gw.azure-api.net/zimax/openai/v1`
* **Key Source**: Azure Key Vault Secret `azure-ai-key`
* **Key Validation**: This key MUST verify against the APIM endpoint, *not* the backend Foundry resource.

**Environment Variable Mapping (`backend/.env`):**

```bash
# Correct Configuration
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_KEY=<APIM_SUBSCRIPTION_KEY> 
AZURE_AI_DEPLOYMENT=gpt-5-chat
```

### 2. GPT Real-Time (VoiceLive)

For real-time audio interaction, use the APIM Gateway endpoint configured for the Real-Time API.

* **Endpoint**: `https://zimax-gw.azure-api.net/zimax`
* **Key Source**: Azure Key Vault Secret `azure-ai-key` (or specific `azure-voicelive-key` if separated)
* **Note**: The client SDK automatically handles the WebSocket upgrade (`wss://`) and path appending (`/openai/realtime`).

**Environment Variable Mapping:**

```bash
AZURE_VOICELIVE_ENDPOINT=https://zimax-gw.azure-api.net/zimax
AZURE_VOICELIVE_KEY=cf23c3ed0f9d420dbd02c1e95a5b5bb3  # Use APIM Key
AZURE_VOICELIVE_MODEL=gpt-realtime
```

## Azure AI GPT-5 Implementation Guide (Reference)

This section contains the **authoritative** configuration for the `gpt-5-chat` model, which uses the Azure AI Responses and Completions APIs.

### Common Environment Variables (Required)

These variables must be set in your `.env` file, GitHub Secrets, and Azure Key Vault.

```bash
AZURE_ENV_NAME="models-playground-7423"
AZURE_LOCATION="eastus2"
AZURE_SUBSCRIPTION_ID="23f4e2c5-0667-4514-8e2e-f02ca7880c95"
AZURE_EXISTING_AIPROJECT_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_EXISTING_AIPROJECT_RESOURCE_ID="/subscriptions/23f4e2c5-0667-4514-8e2e-f02ca7880c95/resourceGroups/zimax-ai/providers/Microsoft.CognitiveServices/accounts/zimax/projects/zimax"
AZURE_EXISTING_RESOURCE_ID="/subscriptions/23f4e2c5-0667-4514-8e2e-f02ca7880c95/resourceGroups/zimax-ai/providers/Microsoft.CognitiveServices/accounts/zimax"
AZD_ALLOW_NON_EMPTY_FOLDER=true
```

### Option A: Responses API (Python)

Use this pattern for advanced agentic behaviors supported by the Responses API.

```python
from openai import OpenAI

endpoint = "https://zimax-gw.azure-api.net/zimax/openai/v1/"
deployment_name = "gpt-5-chat"
api_key = "<your-api-key>" # Source from Key Vault secret: azure-ai-key

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

response = client.responses.create(
    model=deployment_name,
    input="What is the capital of France?",
)

print(f"answer: {response.output[0]}")
```

### Option B: Completions API (Python)

Use this pattern for standard chat completion compatibility.

```python
from openai import OpenAI

endpoint = "https://zimax-gw.azure-api.net/zimax/openai/v1/"
deployment_name = "gpt-5-chat"
api_key = "<your-api-key>" # Source from Key Vault secret: azure-ai-key

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
    temperature=0.7,
)

print(completion.choices[0].message)
```

## Troubleshooting 401 Unauthorized

If an agent returns `401 PermissionDenied`:

1. **Check the Endpoint**: Ensure `AZURE_AI_ENDPOINT` matches `AZURE_EXISTING_AIPROJECT_ENDPOINT` (`https://zimax-gw.azure-api.net/zimax/openai/v1/`).
2. **Check the Key**: Ensure `AZURE_AI_KEY` matches the APIM Subscription Key (`cf23...`), NOT the backend Foundry resource key.
3. **Verify Deployment**: The deployment name must be `gpt-5-chat` (or `gpt-5.1-chat` if explicitly versioned).

## Zep Memory: Sessions vs. Episodes

* **Session**: A continuous thread of conversation between a user and an agent. Identified by a unique `session_id` (UUID). In Engram, a new Session is created for each distinct task or conversation flow initiated by the user.
* **Episode**: A subset of a Session, often demarcated by time or context shifts. Zep automatically segments long Sessions into Episodes for summarization.
  * *Engram Usage*: We primarily track **Sessions**. When a user starts a "New Chat" in the UI, a fresh `session_id` is generated, creating a pristine context window in Zep.

### Best Practice

* **Always** generate a new `session_id` (UUID v4) for a new logical task.
* **Never** reuse `session_id` across different users or unrelated tasks, as this pollutes the context.
