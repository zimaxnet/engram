# Configuration Alignment - Source of Truth

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Configuration Reference

---

## Overview

This document ensures alignment between all configuration sources:
- `.env` files (local development)
- Azure Container Apps environment variables (production)
- GitHub Secrets (CI/CD)
- Azure Key Vault (secrets storage)

---

## Required Configuration Variables

### Azure AI Chat Configuration

| Variable | Value | Source | Notes |
|----------|-------|--------|-------|
| `AZURE_AI_ENDPOINT` | `https://zimax-gw.azure-api.net/zimax/openai/v1/` | All | **Must include `/openai/v1/`** for OpenAI SDK format |
| `AZURE_AI_DEPLOYMENT` | `gpt-5.1-chat` | All | Direct model deployment name |
| `AZURE_AI_KEY` | `cf23c3ed0f9d420dbd02c1e95a5b5bb3` | Key Vault / GitHub Secrets | APIM subscription key |
| `AZURE_AI_API_VERSION` | `2024-12-01-preview` | All | API version (required for gpt-5.1-chat model version 2025-11-13) |
| `AZURE_AI_MODEL_ROUTER` | *(empty or not set)* | All | **Leave empty to use direct model** |

### Important Notes

1. **Endpoint Format**: The endpoint **MUST include `/openai/v1/`** for OpenAI SDK compatibility:
   - ✅ Correct: `https://zimax-gw.azure-api.net/zimax/openai/v1/`
   - ❌ Wrong: `https://zimax-gw.azure-api.net/zimax`

2. **Model Router**: To use direct model (bypass Model Router):
   - Set `AZURE_AI_MODEL_ROUTER` to empty string `""` OR
   - Delete the variable entirely

3. **API Key**: Stored in Azure Key Vault as `azure-ai-key` and referenced via GitHub Secrets

---

## Configuration Sources

### 1. Local Development (.env)

**File:** `.env` (or `.env.local`)

```bash
# Azure AI Chat
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"
AZURE_AI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
AZURE_AI_API_VERSION="2024-12-01-preview"
AZURE_AI_MODEL_ROUTER=""  # Empty = use direct model
```

### 2. Azure Container Apps

**Location:** Azure Portal → Container Apps → `staging-env-api` → Configuration → Environment variables

| Variable | Value |
|----------|-------|
| `AZURE_AI_ENDPOINT` | `https://zimax-gw.azure-api.net/zimax/openai/v1/` |
| `AZURE_AI_DEPLOYMENT` | `gpt-5.1-chat` |
| `AZURE_AI_KEY` | *(from Key Vault reference)* |
| `AZURE_AI_API_VERSION` | `2024-12-01-preview` |
| `AZURE_AI_MODEL_ROUTER` | *(empty or deleted)* |

**Key Vault Reference:**
- Secret name: `azure-ai-key`
- Reference format: `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/azure-ai-key/)`

### 3. GitHub Secrets

**Location:** GitHub → Repository → Settings → Secrets and variables → Actions

| Secret Name | Value | Used For |
|-------------|-------|----------|
| `AZURE_AI_KEY` | `cf23c3ed0f9d420dbd02c1e95a5b5bb3` | CI/CD deployments |
| `AZURE_KEYVAULT_URL` | `https://<vault>.vault.azure.net/` | Key Vault access |

**Note:** GitHub Actions may also reference Key Vault directly via Azure credentials.

### 4. Azure Key Vault

**Location:** Azure Portal → Key Vaults → `<your-keyvault>` → Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `azure-ai-key` | `cf23c3ed0f9d420dbd02c1e95a5b5bb3` | APIM subscription key for chat API |

---

## Verification Checklist

### ✅ Endpoint Format
- [ ] `AZURE_AI_ENDPOINT` includes `/openai/v1/` in all sources
- [ ] Code detects OpenAI-compatible format correctly
- [ ] URL construction: `{endpoint}/chat/completions` (not `/deployments/...`)

### ✅ Model Configuration
- [ ] `AZURE_AI_DEPLOYMENT` is set to `gpt-5.1-chat` in all sources
- [ ] `AZURE_AI_MODEL_ROUTER` is empty or not set (to use direct model)
- [ ] Code uses `model` parameter in payload (not deployment path)

### ✅ Authentication
- [ ] `AZURE_AI_KEY` is set in Key Vault as `azure-ai-key`
- [ ] Container Apps references Key Vault secret correctly
- [ ] GitHub Secrets has `AZURE_AI_KEY` for CI/CD
- [ ] Code uses `Ocp-Apim-Subscription-Key` header for APIM

### ✅ API Version
- [ ] `AZURE_AI_API_VERSION` is set to `2024-12-01-preview` (required for model version 2025-11-13)
- [ ] Version supports `gpt-5.1-chat` model version `2025-11-13`

---

## Code Behavior

### When Endpoint Contains `/openai/v1/`

```python
# backend/agents/base.py - FoundryChatClient
if "/openai/v1" in base:
    # OpenAI-compatible format
    self.url = f"{base}/chat/completions"  # e.g., https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions
    self.is_openai_compat = True
    self.model = deployment  # "gpt-5.1-chat"
    
# Payload includes model parameter
payload = {
    "messages": [...],
    "model": "gpt-5.1-chat"  # ← Model in body
}

# Headers
headers = {
    "Content-Type": "application/json",
    "Ocp-Apim-Subscription-Key": api_key,
    "api-key": api_key
}
```

### Expected Request

```http
POST https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions
Headers:
  Content-Type: application/json
  Ocp-Apim-Subscription-Key: cf23c3ed0f9d420dbd02c1e95a5b5bb3
  api-key: cf23c3ed0f9d420dbd02c1e95a5b5bb3
Body:
{
  "messages": [{"role": "user", "content": "What is the capital of France?"}],
  "model": "gpt-5.1-chat",
  "temperature": 0.7,
  "max_tokens": 4096
}
```

---

## Alignment Script

Use this script to verify configuration alignment:

```bash
# Check Azure Container Apps environment variables
az containerapp show \
  --name staging-env-api \
  --resource-group <resource-group> \
  --query "properties.template.containers[0].env" \
  --output table

# Check Key Vault secret
az keyvault secret show \
  --vault-name <vault-name> \
  --name azure-ai-key \
  --query "value" \
  --output tsv
```

---

## Troubleshooting

### Issue: 400 Bad Request
- **Check**: Endpoint format includes `/openai/v1/`
- **Check**: Model name matches deployment (`gpt-5.1-chat`)
- **Check**: API key is correct

### Issue: Model Router Still Active
- **Check**: `AZURE_AI_MODEL_ROUTER` is empty or deleted
- **Check**: Logs show "Using direct model deployment" (not "Using Model Router")

### Issue: Authentication Failed
- **Check**: Key Vault secret `azure-ai-key` exists and is correct
- **Check**: Container Apps has Key Vault reference configured
- **Check**: Managed Identity has Key Vault access

---

## Related Documentation

- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router
- `docs/sop/azure-foundry-chat-sop.md` - Model Router configuration
- `backend/agents/base.py` - FoundryChatClient implementation
- `backend/core/config.py` - Settings definition

