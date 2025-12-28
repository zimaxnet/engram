# Fix Chat for Enterprise POC Deployment

## Current Status

✅ **Configuration Set:**
- `AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1`
- `AZURE_AI_MODEL_ROUTER=model-router`
- `AZURE_AI_KEY` (secret reference to Key Vault)

❌ **Issue:**
- Chat returns 401 PermissionDenied
- Backend is calling Model Router but getting authentication error

## Root Cause Analysis

The 401 error indicates an authentication problem. Possible causes:

1. **API Key Mismatch**: The Key Vault secret `azure-ai-key` may contain:
   - Foundry direct key (wrong for APIM Gateway)
   - Expired or invalid key
   - Wrong subscription key

2. **Endpoint URL Issue**: The endpoint format may need adjustment

3. **Model Router Deployment**: The deployment name `model-router` may not exist or be accessible

## Enterprise-Grade Fix

### Step 1: Verify API Key

The API key in Key Vault must be the **APIM Gateway Subscription Key**, not the Foundry direct key.

```bash
# Check current key (first 8 chars only for security)
az keyvault secret show \
  --vault-name <key-vault-name> \
  --name azure-ai-key \
  --query "value" \
  --output tsv | head -c 8
```

**Required**: APIM Gateway subscription key that works with:
- Endpoint: `https://zimax-gw.azure-api.net/zimax/openai/v1`
- Header: `Ocp-Apim-Subscription-Key: <key>`

### Step 2: Verify Model Router Deployment

Confirm the Model Router deployment name is correct:

```bash
# Check if model-router deployment exists in APIM
# This requires access to Azure Portal or APIM management API
```

### Step 3: Test Direct API Call

Test the Model Router directly to isolate the issue:

```bash
# Get API key from Key Vault
API_KEY=$(az keyvault secret show \
  --vault-name <key-vault-name> \
  --name azure-ai-key \
  --query "value" \
  --output tsv)

# Test Model Router via APIM Gateway
curl -X POST "https://zimax-gw.azure-api.net/zimax/openai/v1/chat/completions" \
  -H "Ocp-Apim-Subscription-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model-router",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Step 4: Update Key Vault Secret (if needed)

If the key is wrong, update it:

```bash
# Update with correct APIM subscription key
az keyvault secret set \
  --vault-name <key-vault-name> \
  --name azure-ai-key \
  --value "<correct-apim-subscription-key>"
```

### Step 5: Restart Container App

After updating the key:

```bash
az containerapp revision restart \
  --name staging-env-api \
  --resource-group engram-rg \
  --revision <latest-revision>
```

## Verification Checklist

- [ ] API key is APIM Gateway subscription key (not Foundry direct key)
- [ ] Endpoint URL is correct: `https://zimax-gw.azure-api.net/zimax/openai/v1`
- [ ] Model Router deployment name is correct: `model-router`
- [ ] Direct API call to Model Router succeeds
- [ ] Container App has latest environment variables
- [ ] Container App restarted after key update
- [ ] Chat endpoint returns successful response

## Expected Behavior

After fixes:
1. Backend logs show: `"Using Model Router via APIM Gateway: model-router"`
2. Chat requests succeed with HTTP 200
3. Elena responds with actual content (not error message)
4. No 401 errors in logs

## Enterprise Deployment Requirements

For enterprise POC, ensure:
- ✅ All configuration is in Key Vault (not hardcoded)
- ✅ Environment variables are set via Bicep/Infrastructure
- ✅ API keys are rotated regularly
- ✅ Error logging is comprehensive
- ✅ Health checks validate configuration
- ✅ Monitoring alerts on authentication failures

