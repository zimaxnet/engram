# Azure AI Configuration & Troubleshooting SOP

## Overview

Engram uses a dual-path approach for Azure AI integration:

1. **Azure API Management (APIM)**: The primary gateway for standard LLM calls (OpenAI-compatible). This provides rate limiting, monitoring, and unified access control.
2. **Azure AI Foundry (Direct)**: Used for specialized services like "VoiceLive" (Real-time API) that require direct WebSocket connections or features not yet supported by the APIM gateway.

## Configuration Standards

### 1. Azure AI Foundry Model Router (Recommended for Chat)

For standard agent chat, the backend can use **Azure AI Foundry Model Router** for intelligent model selection and cost optimization.

**Option A: Model Router via APIM Gateway (Recommended)**

* **Endpoint**: `https://zimax-gw.azure-api.net/zimax/openai/v1`
* **Model Router**: Deployed Model Router deployment name (e.g., `model-router`)
* **Key Source**: Azure Key Vault Secret `azure-ai-key` (APIM Subscription Key)
* **Available APIs**: 
  - Chat Completions API (`/chat/completions`) - Used by Engram agents
  - Responses API (`/responses`) - Simpler input/output format

**Environment Variable Mapping (`backend/.env`):**

```bash
# Model Router via APIM Gateway (Recommended)
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_MODEL_ROUTER=model-router  # Model Router deployment name
AZURE_AI_KEY=<APIM_SUBSCRIPTION_KEY>
```

**API Examples:**

```python
# Chat Completions API (used by Engram agents)
from openai import OpenAI

client = OpenAI(
    base_url="https://zimax-gw.azure-api.net/zimax/openai/v1/",
    api_key="<your-api-key>"
)

completion = client.chat.completions.create(
    model="model-router",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
    temperature=0.7,
)

# Responses API (simpler format)
response = client.responses.create(
    model="model-router",
    input="What is the capital of France?",
)
print(f"answer: {response.output[0]}")
```

**Option B: Model Router via Foundry Direct**

* **Endpoint**: `https://zimax.services.ai.azure.com/` (Direct Cognitive Services)
* **Project**: Set if using project-based endpoints
* **Model Router**: Deployed Model Router deployment name (e.g., `model-router-prod`)
* **Key Source**: Azure Key Vault Secret `azure-ai-key` (Cognitive Services key)

**Environment Variable Mapping (`backend/.env`):**

```bash
# Model Router via Foundry Direct
AZURE_AI_ENDPOINT=https://zimax.services.ai.azure.com/
AZURE_AI_PROJECT_NAME=zimax  # Optional, if using project-based endpoints
AZURE_AI_MODEL_ROUTER=model-router-prod  # Model Router deployment name
AZURE_AI_KEY=<Cognitive-Services-Key>
AZURE_AI_API_VERSION=2024-10-01-preview
```

**Benefits:**
- Dynamic model selection based on query complexity
- Cost optimization (routes simple queries to cheaper models)
- Automatic fallback and load balancing
- Single endpoint for multiple models
- Works with APIM Gateway for unified access control and monitoring

### 1a. Azure APIM Gateway (Alternative for Chat)

For standard agent chat (`gpt-5-chat`, `gpt-4o`), the backend can also connect via the APIM Gateway.

* **Endpoint**: `https://zimax-gw.azure-api.net/zimax/openai/v1`
* **Key Source**: Azure Key Vault Secret `azure-ai-key`
* **Key Validation**: This key MUST verify against the APIM endpoint, *not* the backend Foundry resource.

**Environment Variable Mapping (`backend/.env`):**

```bash
# APIM Gateway Configuration (Alternative)
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_KEY=<APIM_SUBSCRIPTION_KEY> 
AZURE_AI_DEPLOYMENT=gpt-5-chat
```

### 2. GPT Real-Time (VoiceLive)

> [!IMPORTANT]
> **VoiceLive uses completely separate configuration from chat.** The Model Router and chat endpoint settings do NOT affect VoiceLive.

For real-time audio interaction, use the **Direct Cognitive Services endpoint** (not APIM, not Model Router).

> [!IMPORTANT]
> After extensive debugging (December 2025), we determined that VoiceLive works reliably with the Direct Endpoint and API Key, NOT the APIM gateway. APIM returns 404 for the realtime model.

* **Endpoint**: `https://zimax.services.ai.azure.com/` (Direct Cognitive Services)
* **Key Source**: Azure Key Vault Secret `voicelive-api-key` (Cognitive Services key, NOT APIM key)
* **Model**: `gpt-realtime`
* **Note**: The `azure-ai-voicelive` SDK handles WebSocket upgrade and path construction.

**Environment Variable Mapping:**

```bash
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com/
AZURE_VOICELIVE_KEY=<Cognitive-Services-Key>  # NOT the APIM key
AZURE_VOICELIVE_MODEL=gpt-realtime
```

**Key Retrieval:**

```bash
# Get the correct key for VoiceLive
az cognitiveservices account keys list \
  --name zimax \
  --resource-group zimax-ai \
  --query "key1" -o tsv
```

> See [VoiceLive Configuration SOP](./voicelive-configuration.md) for detailed troubleshooting.

### 3. Anthropic Claude API (Story Generation)

Sage uses Anthropic's Claude for creative story generation.

* **Endpoint**: `https://api.anthropic.com/v1` (Direct Anthropic API)
* **Key Source**: Azure Key Vault Secret `anthropic-api-key` or Container Apps secret
* **Model**: `claude-3-sonnet` or `claude-3-opus`

**Environment Variable Mapping:**

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**Setting in Azure Container Apps:**

```bash
# Set secret for API and Worker containers
az containerapp secret set --name staging-env-api --resource-group engram-rg \
  --secrets "anthropic-api-key=<your-key>"
  
az containerapp secret set --name staging-env-worker --resource-group engram-rg \
  --secrets "anthropic-api-key=<your-key>"

# Restart containers to pick up new secret
az containerapp update --name staging-env-api --resource-group engram-rg \
  --set-env-vars "KEY_REFRESH_TS=$(date +%s)"
```

> [!NOTE]
> After setting secrets, you must create a new revision (update with env var change) for the container to pick up the new value.

---

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

## Troubleshooting Chat Issues

### Common Error: "I apologize, but I encountered an issue processing your request"

This generic error message indicates the chat endpoint caught an exception. Check the backend logs for detailed error information.

#### 1. Check Environment Variables

Verify all required environment variables are set in Azure Container Apps:

```bash
# Required for Model Router via APIM Gateway
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_MODEL_ROUTER=model-router  # If using Model Router
AZURE_AI_KEY=<APIM_SUBSCRIPTION_KEY>  # Must be APIM key, not Foundry key
AZURE_AI_API_VERSION=2024-10-01-preview
```

#### 2. Test Model Router Configuration

Use the diagnostic script to test the configuration:

```bash
python3 scripts/test-chat-model-router.py
```

This will:
- Verify environment variables are set
- Test the API endpoint connectivity
- Validate authentication
- Test agent chat functionality

#### 3. Verify APIM Subscription Key

The `AZURE_AI_KEY` must be the **APIM Subscription Key**, not the Cognitive Services key:

```bash
# Get APIM subscription key from Azure Portal
# Or from Key Vault secret: azure-ai-key
```

#### 4. Check Model Router Deployment Name

If using Model Router, verify the deployment name matches exactly:

```bash
# In Azure AI Foundry, check the Model Router deployment name
# It should match AZURE_AI_MODEL_ROUTER exactly (case-sensitive)
```

#### 5. Verify Endpoint Format

For APIM Gateway, the endpoint must include `/openai/v1`:

```bash
# Correct
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1

# Incorrect (missing /openai/v1)
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax
```

#### 6. Check Backend Logs

View detailed error logs in Azure Container Apps:

```bash
# View logs for API container
az containerapp logs show \
  --name staging-env-api \
  --resource-group engram-rg \
  --follow

# Look for errors like:
# - "FoundryChatClient: Error calling LLM"
# - "Agent execution failed"
# - HTTP status codes (401, 404, 500)
```

#### 7. Test Direct API Call

Test the Model Router API directly:

```bash
curl -X POST "https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions" \
  -H "Ocp-Apim-Subscription-Key: <APIM_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model-router",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Troubleshooting 401 Unauthorized

If an agent returns `401 PermissionDenied`:

1. **Check the Endpoint**: Ensure `AZURE_AI_ENDPOINT` matches `AZURE_EXISTING_AIPROJECT_ENDPOINT` (`https://zimax-gw.azure-api.net/zimax/openai/v1/`).
2. **Check the Key**: Ensure `AZURE_AI_KEY` matches the APIM Subscription Key (`cf23...`), NOT the backend Foundry resource key.
3. **Verify Deployment**: The deployment name must match exactly (e.g., `model-router` for Model Router, or `gpt-5-chat` for direct deployment).

## Zep Memory: Sessions vs. Episodes

* **Session**: A continuous thread of conversation between a user and an agent. Identified by a unique `session_id` (UUID). In Engram, a new Session is created for each distinct task or conversation flow initiated by the user.
* **Episode**: A subset of a Session, often demarcated by time or context shifts. Zep automatically segments long Sessions into Episodes for summarization.
  * *Engram Usage*: We primarily track **Sessions**. When a user starts a "New Chat" in the UI, a fresh `session_id` is generated, creating a pristine context window in Zep.

### Best Practice

* **Always** generate a new `session_id` (UUID v4) for a new logical task.
* **Never** reuse `session_id` across different users or unrelated tasks, as this pollutes the context.
