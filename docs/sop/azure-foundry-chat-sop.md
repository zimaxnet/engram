# Azure Foundry Chat (Model Router) SOP

> **Last Updated**: December 2025  
> **Status**: Enterprise POC  
> **Maintainer**: Engram Platform Team

## Overview

This SOP establishes the OpenAI-compatible chat flow for Azure AI Foundry Model Router using the APIM gateway and key authentication. It is the reference path for enterprise POC chat reliability.

## Scope

- Chat Completions API for Engram agents and validation
- Azure AI Foundry Model Router (deployment name: `model-router`)
- APIM gateway front door (`/openai/v1`) with subscription key auth
- Does not cover VoiceLive (see `docs/sop/voicelive-configuration.md`)

## Prerequisites

- Azure AI Foundry project with a deployed Model Router named `model-router`
- APIM Gateway routing to the Foundry OpenAI-compatible endpoint
- APIM subscription key stored in Azure Key Vault (do not hardcode)
- If using direct Foundry endpoint, a project name (e.g., `zimax`)

## Required Environment Variables

### Runtime (Chat)

```bash
# Required for chat via APIM (recommended)
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_AI_MODEL_ROUTER="model-router"
AZURE_AI_KEY="<APIM_SUBSCRIPTION_KEY>"
AZURE_AI_API_VERSION="2024-10-01-preview"

# Optional (only for direct Foundry endpoints)
AZURE_AI_PROJECT_NAME="zimax"
```

> [!IMPORTANT]
> Use the APIM subscription key for `AZURE_AI_KEY` when routing via APIM. Do not use the Foundry resource key here.

### Provisioning (AZD / Environment)

```bash
AZURE_ENV_NAME="models-playground-5303"
AZURE_LOCATION="eastus2"
AZURE_SUBSCRIPTION_ID="<SUBSCRIPTION_ID>"
AZURE_EXISTING_AIPROJECT_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_EXISTING_AIPROJECT_RESOURCE_ID="<RESOURCE_ID>"
AZURE_EXISTING_RESOURCE_ID="<RESOURCE_ID>"
AZD_ALLOW_NON_EMPTY_FOLDER=true
```

## Key Vault Setup

```bash
az keyvault secret set \
  --vault-name <your-keyvault> \
  --name azure-ai-key \
  --value "<APIM_SUBSCRIPTION_KEY>"
```

## API Validation (curl)

```bash
curl -X POST "https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Ocp-Apim-Subscription-Key: <APIM_SUBSCRIPTION_KEY>" \
  -d '{
    "model": "model-router",
    "messages": [{"role": "user", "content": "What is the capital of France?"}]
  }'
```

Expected: HTTP 200 with a JSON response containing `choices[0].message`.

## Python Validation (OpenAI SDK)

```python
from openai import OpenAI

endpoint = "https://zimax-gw.azure-api.net/zimax/openai/v1/"
deployment_name = "model-router"
api_key = "<APIM_SUBSCRIPTION_KEY>"

client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {"role": "user", "content": "What is the capital of France?"},
    ],
    temperature=0.7,
)

print(completion.choices[0].message)
```

### If APIM requires a subscription key header

Some APIM policies require `Ocp-Apim-Subscription-Key` or `api-key`. Use default headers:

```python
client = OpenAI(
    base_url=endpoint,
    api_key="unused",
    default_headers={"Ocp-Apim-Subscription-Key": api_key},
)
```

## Engram Backend Verification

1. Set the chat variables in `backend/.env` (or Key Vault).
2. Ensure `AZURE_AI_MODEL_ROUTER` is set; this forces Model Router usage.
3. For APIM endpoints, do not set `AZURE_AI_PROJECT_NAME`.
4. Start the API and check logs for:
   - `Using Model Router via APIM Gateway: model-router`
   - `FoundryChatClient: Response status=200`

## Troubleshooting

### 401 Unauthorized

- Ensure the key is the APIM subscription key, not the Foundry resource key.
- If using SDK, confirm APIM accepts `Authorization` or use `default_headers`.

### 404 Not Found

- Verify endpoint includes `/openai/v1/` and the route exists in APIM.
- Confirm deployment name is exactly `model-router`.

### 400 Bad Request

- Ensure the `model` field is present in the request body.
- Confirm payload matches OpenAI chat format (roles: `system`, `user`, `assistant`).

### 429 Too Many Requests

- APIM rate limiting is triggered. Request higher limits or reduce concurrency.

## Enterprise POC Readiness Checklist

- [ ] Model Router deployment exists and is accessible
- [ ] APIM gateway routes `/openai/v1/chat/completions`
- [ ] APIM subscription key stored in Key Vault
- [ ] `.env` / container env vars updated with Model Router values
- [ ] curl and Python SDK validations return HTTP 200
