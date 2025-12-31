# Configuration Quick Reference

**Last Updated:** December 31, 2025

---

## ✅ Correct Configuration (Working)

```bash
# Endpoint MUST include /openai/v1/ for OpenAI SDK format
AZURE_AI_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
AZURE_AI_DEPLOYMENT="gpt-5.1-chat"
AZURE_AI_MODEL_ROUTER=""  # Empty = use direct model
AZURE_AI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
AZURE_AI_API_VERSION="2024-12-01-preview"
```

---

## 🔍 Verification

### Check Container App Config
```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env" \
  --output table
```

### Check Key Vault Secret
```bash
az keyvault secret show \
  --vault-name <vault-name> \
  --name azure-ai-key \
  --query "value" \
  --output tsv
```

### Run Verification Script
```bash
./scripts/verify-config-alignment.sh
```

---

## 📋 Configuration Checklist

- [ ] `AZURE_AI_ENDPOINT` includes `/openai/v1/`
- [ ] `AZURE_AI_DEPLOYMENT` is `gpt-5.1-chat`
- [ ] `AZURE_AI_MODEL_ROUTER` is empty or deleted
- [ ] `AZURE_AI_KEY` is stored in Key Vault as `azure-ai-key`
- [ ] Container App references Key Vault secret correctly

---

## 🔧 Quick Fixes

### Fix Endpoint Format
```bash
# In Azure Portal: Container Apps → Configuration → Environment variables
# Set AZURE_AI_ENDPOINT to: https://zimax-gw.azure-api.net/zimax/openai/v1/
```

### Disable Model Router
```bash
# In Azure Portal: Container Apps → Configuration → Environment variables
# Delete AZURE_AI_MODEL_ROUTER OR set to empty string ""
```

### Update Key Vault Secret
```bash
az keyvault secret set \
  --vault-name <vault-name> \
  --name azure-ai-key \
  --value "cf23c3ed0f9d420dbd02c1e95a5b5bb3"
```

---

## 📚 Full Documentation

- `docs/configuration/config-alignment.md` - Complete alignment guide
- `docs/troubleshooting/bypass-model-router.md` - Disable Model Router
- `docs/sop/azure-foundry-chat-sop.md` - Chat API configuration

