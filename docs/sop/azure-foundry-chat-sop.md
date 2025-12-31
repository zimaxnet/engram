# Azure Foundry Chat (Model Router) SOP

> **Last Updated**: December 31, 2025  
> **Status**: Enterprise POC - Verified Working  
> **Maintainer**: Engram Platform Team  
> **API Version**: `2024-12-01-preview` (updated December 31, 2025 - required for o4-mini)

## Overview

This SOP establishes the chat flow for Azure AI Foundry Model Router using the APIM gateway. It documents the **Azure OpenAI SDK format** (not OpenAI SDK format) which is the verified working configuration.

## Scope

- Chat Completions API for Engram agents (Elena, Marcus, Sage)
- Azure AI Foundry Model Router (deployment name: `model-router`)
- APIM gateway front door with subscription key auth
- Does not cover VoiceLive (see `docs/sop/voicelive-configuration.md`)

## Key Distinction: Azure OpenAI vs OpenAI SDK Format

> [!IMPORTANT]
> The APIM gateway uses **Azure OpenAI SDK format**, NOT OpenAI SDK format.
>
> | Format | Endpoint Pattern | Model in Body? |
> |--------|------------------|----------------|
> | **Azure OpenAI** (correct) | `/openai/deployments/{model}/chat/completions?api-version=...` | No |
> | OpenAI SDK (wrong) | `/chat/completions` with `model` param | Yes |

## Prerequisites

- Azure AI Foundry project with a deployed Model Router named `model-router`
- APIM Gateway routing to the Azure OpenAI endpoint
- APIM subscription key stored in Azure Key Vault (secret name: `azure-ai-key`)

## Required Environment Variables

### Runtime (Chat)

```bash
# Required for chat via APIM (OpenAI SDK format)
# IMPORTANT: Endpoint MUST include /openai/v1/ for OpenAI SDK compatibility
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"
AZURE_AI_MODEL_ROUTER=""  # Empty = use direct model (bypass Model Router)
AZURE_AI_KEY="<APIM_SUBSCRIPTION_KEY>"
AZURE_AI_API_VERSION="2024-12-01-preview"

# NOT USED for APIM gateway (leave empty)
AZURE_AI_PROJECT_NAME=""
```

> [!IMPORTANT]
> **Endpoint Format**: The endpoint **MUST include `/openai/v1/`** for OpenAI SDK format compatibility.
> - ✅ Correct: `https://zimax-gw.azure-api.net/zimax/openai/v1/`
> - ❌ Wrong: `https://zimax-gw.azure-api.net/zimax`
>
> **Model Router**: Set `AZURE_AI_MODEL_ROUTER` to empty string `""` or delete it to use direct model deployment.

> [!IMPORTANT]
>
> - `AZURE_AI_ENDPOINT` is the **base URL only** (no `/openai/v1`)
> - The backend constructs: `{endpoint}/openai/deployments/{model}/chat/completions?api-version=...`
> - Use the APIM subscription key, not the Foundry resource key

## Key Vault Setup

```bash
az keyvault secret set \
  --vault-name <your-keyvault> \
  --name azure-ai-key \
  --value "<APIM_SUBSCRIPTION_KEY>"
```

## API Validation (curl)

### Azure OpenAI Format (Correct)

```bash
curl -X POST "https://zimax-gw.azure-api.net/zimax/openai/deployments/model-router/chat/completions?api-version=2024-12-01-preview" \
  -H "Content-Type: application/json" \
  -H "api-key: <APIM_SUBSCRIPTION_KEY>" \
  -d '{
    "messages": [{"role": "user", "content": "What is the capital of France?"}]
  }'
```

Expected: HTTP 200 with a JSON response containing `choices[0].message`.

## Python Validation (Azure OpenAI SDK)

```python
from openai import AzureOpenAI

endpoint = "https://zimax-gw.azure-api.net/zimax"
deployment = "model-router"
api_key = "<APIM_SUBSCRIPTION_KEY>"

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-12-01-preview",
)

completion = client.chat.completions.create(
    model=deployment,
    messages=[
        {"role": "user", "content": "What is the capital of France?"},
    ],
)

print(completion.choices[0].message)
```

## Engram Backend Configuration

The backend `FoundryChatClient` automatically detects endpoint format:

1. If endpoint contains `/openai/v1` → OpenAI SDK format (model in body)
2. Otherwise → Azure OpenAI format (model in URL path)

### Correct Configuration

```bash
# In Azure Container Apps or .env
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax
AZURE_AI_DEPLOYMENT=model-router
AZURE_AI_MODEL_ROUTER=model-router
AZURE_AI_API_VERSION=2024-10-01-preview
AZURE_AI_PROJECT_NAME=  # Empty
```

### Verification

Check logs for:

```
FoundryChatClient: Calling https://zimax-gw.azure-api.net/zimax/openai/deployments/model-router/chat/completions?api-version=2024-12-01-preview
FoundryChatClient: is_openai_compat=False, model=None
FoundryChatClient: Response status=200
```

## Troubleshooting

### 401 Unauthorized (API)

- Ensure using APIM subscription key, not Foundry resource key
- Check `api-key` header is set correctly

### 401 Unauthorized (Platform Auth)

Azure Container Apps Platform Authentication may block requests. Disable with:

```bash
az containerapp auth update \
  --name staging-env-api \
  --resource-group engram-rg \
  --unauthenticated-client-action AllowAnonymous \
  --enabled false
```

### 404 Not Found

- Verify endpoint is base URL only (no `/openai/v1`)
- Confirm deployment name is exactly `model-router`

### 400 Bad Request

- For Azure OpenAI format, `model` should NOT be in request body
- Confirm payload uses correct message format

## Infrastructure (Bicep)

```bicep
// In backend-aca.bicep
param azureAiEndpoint string = 'https://zimax-gw.azure-api.net/zimax'
param azureAiModelRouter string = 'model-router'

// Environment variables
{
  name: 'AZURE_AI_ENDPOINT'
  value: azureAiEndpoint
}
{
  name: 'AZURE_AI_DEPLOYMENT'
  value: 'model-router'
}
{
  name: 'AZURE_AI_MODEL_ROUTER'
  value: azureAiModelRouter
}
{
  name: 'AZURE_AI_PROJECT_NAME'
  value: ''  // Empty for APIM gateway
}
```

## Enterprise POC Readiness Checklist

- [x] Model Router deployment exists (`model-router`)
- [x] APIM gateway routes `/openai/deployments/model-router/chat/completions`
- [x] APIM subscription key stored in Key Vault
- [x] Container env vars use Azure OpenAI format
- [x] Platform Auth disabled (AllowAnonymous)
- [x] curl validation returns HTTP 200
- [x] Chat verified working (December 27, 2025)

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | **Updated API version**: Changed to `2024-12-01-preview` (required for o4-mini model selected by Model Router) |
| 2025-12-31 | **Updated API version**: Changed from `2024-05-01-preview` to `2024-10-01-preview` (newer API version) |
| 2025-12-27 | **Fixed endpoint format**: Changed from OpenAI SDK format (`/openai/v1`) to Azure OpenAI format (base URL only) |
| 2025-12-27 | **Fixed 401 Platform Auth**: Disabled Azure EasyAuth that was blocking API requests |
| 2025-12-27 | **Verified working**: Chat successfully tested with model-router |
| 2025-12-27 | Initial SOP creation |
