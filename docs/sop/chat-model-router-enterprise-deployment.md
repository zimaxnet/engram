# Chat Model Router Enterprise Deployment Guide

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Classification:** Enterprise Operations  
**Compliance:** NIST AI RMF, SOC2 Type II

---

## Overview

This guide provides step-by-step instructions for deploying and validating the Chat Model Router configuration for enterprise deployment and customer presentation.

## Prerequisites

- Azure subscription with appropriate permissions
- Azure AI Foundry Model Router deployed
- APIM Gateway configured with Model Router backend
- Azure Container Apps environment ready
- Access to Azure Key Vault

---

## 1. Configuration Requirements

### Required Environment Variables

Set these environment variables in Azure Container Apps:

```bash
# Model Router via APIM Gateway (REQUIRED for enterprise)
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_MODEL_ROUTER=model-router
AZURE_AI_KEY=<APIM_SUBSCRIPTION_KEY>  # Store in Key Vault
AZURE_AI_API_VERSION=2024-10-01-preview
```

### Key Vault Secret Configuration

Store the APIM subscription key in Azure Key Vault:

```bash
# Create/update secret in Key Vault
az keyvault secret set \
  --vault-name <your-key-vault> \
  --name azure-ai-key \
  --value <APIM_SUBSCRIPTION_KEY>
```

### Container Apps Secret Reference

Reference the Key Vault secret in Container Apps:

```bash
# Set secret reference in Container App
az containerapp secret set \
  --name staging-env-api \
  --resource-group engram-rg \
  --secrets "azure-ai-key=keyvaultref:<key-vault-uri>,azure-ai-key"

# Set environment variable to use the secret
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars \
    "AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1" \
    "AZURE_AI_MODEL_ROUTER=model-router" \
    "AZURE_AI_API_VERSION=2024-10-01-preview" \
    "AZURE_AI_KEY=secretref:azure-ai-key"
```

---

## 2. Validation Steps

### Step 1: Run Enterprise Validation Script

```bash
# From the repository root
./scripts/validate-chat-enterprise-deployment.sh
```

This script validates:
- ✅ Environment variables are set correctly
- ✅ Endpoint format is correct (APIM Gateway)
- ✅ Model Router is configured
- ✅ API connectivity works
- ✅ Configuration is consistent

### Step 2: Test API Connectivity Directly

```bash
# Test Model Router API
curl -X POST "https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions" \
  -H "Ocp-Apim-Subscription-Key: <APIM_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model-router",
    "messages": [{"role": "user", "content": "Hello, this is a test."}]
  }'
```

Expected response: HTTP 200 with JSON containing chat completion.

### Step 3: Test Agent Chat Endpoint

```bash
# Test the Engram chat API
curl -X POST "https://<YOUR_API_FQDN>/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "content": "Hello, this is a test message.",
    "agent_id": "elena",
    "session_id": "test-session-123"
  }'
```

Expected response: HTTP 200 with agent response.

### Step 4: Verify Logs

Check Container Apps logs for successful Model Router usage:

```bash
az containerapp logs show \
  --name staging-env-api \
  --resource-group engram-rg \
  --follow

# Look for:
# - "Using Model Router via APIM Gateway: model-router"
# - "FoundryChatClient: Response status=200"
# - No errors or exceptions
```

---

## 3. Troubleshooting

### Issue: "I apologize, but I encountered an issue processing your request"

**Diagnosis:**
1. Check Container Apps logs for detailed error
2. Verify environment variables are set correctly
3. Test API connectivity directly

**Solution:**
```bash
# Run diagnostic script
python3 scripts/test-chat-model-router.py

# Check logs
az containerapp logs show --name staging-env-api --resource-group engram-rg --follow
```

### Issue: 401 Unauthorized

**Cause:** Incorrect API key or wrong key type.

**Solution:**
- Verify `AZURE_AI_KEY` is the APIM Subscription Key (not Foundry key)
- Ensure Key Vault secret is correctly referenced
- Test key directly with curl

### Issue: 404 Not Found

**Cause:** Incorrect endpoint or Model Router deployment name.

**Solution:**
- Verify endpoint includes `/openai/v1`
- Verify `AZURE_AI_MODEL_ROUTER` matches deployment name exactly
- Check APIM Gateway routing configuration

### Issue: Model Router Not Being Used

**Cause:** `AZURE_AI_MODEL_ROUTER` not set.

**Solution:**
```bash
# Set environment variable
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars "AZURE_AI_MODEL_ROUTER=model-router"

# Restart container to pick up changes
az containerapp revision restart \
  --name staging-env-api \
  --resource-group engram-rg
```

---

## 4. Production Readiness Checklist

Before customer presentation, verify:

- [ ] All environment variables set correctly
- [ ] Enterprise validation script passes (0 errors, 0 warnings)
- [ ] API connectivity test succeeds
- [ ] Agent chat endpoint responds correctly
- [ ] Logs show Model Router being used
- [ ] No errors in Container Apps logs
- [ ] Key Vault secrets properly configured
- [ ] CORS configured for frontend origin
- [ ] Authentication configured (if required)
- [ ] Monitoring and alerting configured

---

## 5. Customer Presentation Demo

### Pre-Demo Checklist

1. **Run validation script** - Ensure all tests pass
2. **Test chat functionality** - Send a test message to Elena
3. **Check logs** - Verify no errors
4. **Prepare demo scenarios** - Have 2-3 conversation examples ready

### Demo Flow

1. **Show Model Router in UI** - Point out "Model Router" in top-right navigation
2. **Start conversation** - Chat with Elena about a business requirement
3. **Show intelligent routing** - Explain how Model Router selects the best model
4. **Demonstrate cost optimization** - Show how simple queries use cheaper models

### Talking Points

- **Model Router Benefits:**
  - Intelligent model selection based on query complexity
  - Automatic cost optimization
  - Single endpoint for multiple models
  - Unified access control via APIM Gateway

- **Enterprise Features:**
  - Secure key management via Key Vault
  - Managed Identity support
  - Comprehensive logging and monitoring
  - Production-ready configuration

---

## 6. Monitoring and Maintenance

### Key Metrics to Monitor

- API response times
- Error rates (should be < 1%)
- Model Router selection patterns
- Cost per conversation
- Container App health

### Regular Maintenance

- **Weekly:** Review logs for errors
- **Monthly:** Review cost optimization metrics
- **Quarterly:** Review Model Router configuration and update if needed

---

## 7. Support and Escalation

### Common Issues

See [Azure AI Configuration SOP](./azure-ai-configuration.md) for detailed troubleshooting.

### Escalation Path

1. Check logs and run diagnostic scripts
2. Review this deployment guide
3. Check Azure AI Configuration SOP
4. Contact Azure support if APIM Gateway issues

---

## Appendix: Quick Reference

### Environment Variables

```bash
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_MODEL_ROUTER=model-router
AZURE_AI_KEY=<APIM_SUBSCRIPTION_KEY>  # From Key Vault
AZURE_AI_API_VERSION=2024-10-01-preview
```

### Validation Commands

```bash
# Run enterprise validation
./scripts/validate-chat-enterprise-deployment.sh

# Test API directly
curl -X POST "https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions" \
  -H "Ocp-Apim-Subscription-Key: <KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model": "model-router", "messages": [{"role": "user", "content": "Hello"}]}'

# Check logs
az containerapp logs show --name staging-env-api --resource-group engram-rg --follow
```

---

**Document Status:** ✅ Validated and Production-Ready  
**Last Validated:** December 2025  
**Next Review:** January 2026

