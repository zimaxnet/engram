---
layout: default
title: Foundry Configuration Setup - Source of Truth
parent: Architecture
nav_order: 10
---

# Foundry Configuration Setup - Source of Truth

> **Last Updated**: January 2026  
> **Principle**: Key Vault is the single source of truth for production

---

## Configuration Values

Based on your Foundry setup:

- **Endpoint**: `https://zimax.services.ai.azure.com`
- **Project**: `zimax`
- **Region**: `eastus2`
- **Elena Agent ID**: `cf23c3ed0f9d420dbd02c1e95a5b5bb3` (if this is Elena's agent ID)

---

## Source of Truth Strategy

### 1. **Azure Key Vault** (Production Source of Truth) ✅

**Store these secrets in Key Vault**:

```bash
# Set secrets in Key Vault
az keyvault secret set \
  --vault-name "staging-env-kv" \
  --name "azure-foundry-agent-endpoint" \
  --value "https://zimax.services.ai.azure.com"

az keyvault secret set \
  --vault-name "staging-env-kv" \
  --name "azure-foundry-agent-project" \
  --value "zimax"

az keyvault secret set \
  --vault-name "staging-env-kv" \
  --name "elena-foundry-agent-id" \
  --value "cf23c3ed0f9d420dbd02c1e95a5b5bb3"

# Optional: API key (if using key auth instead of Managed Identity)
az keyvault secret set \
  --vault-name "staging-env-kv" \
  --name "azure-foundry-agent-key" \
  --value "<api-key>"
```

**Why Key Vault**:
- ✅ Single source of truth for production
- ✅ Secure storage with RBAC
- ✅ Managed Identity access (no keys in code)
- ✅ Easy rotation
- ✅ Audit logging

---

### 2. **GitHub Secrets** (CI/CD Deployment)

**Add to GitHub Repository Secrets**:

1. Go to: GitHub → Repository → Settings → Secrets and variables → Actions
2. Add these secrets:

| Secret Name | Value | Purpose |
|------------|-------|---------|
| `AZURE_FOUNDRY_AGENT_ENDPOINT` | `https://zimax.services.ai.azure.com` | Used in Bicep deployment |
| `AZURE_FOUNDRY_AGENT_PROJECT` | `zimax` | Used in Bicep deployment |
| `AZURE_FOUNDRY_AGENT_KEY` | `<optional-api-key>` | Optional, if using key auth |
| `ELENA_FOUNDRY_AGENT_ID` | `cf23c3ed0f9d420dbd02c1e95a5b5bb3` | Elena's Foundry agent ID |

**Why GitHub Secrets**:
- ✅ Used during deployment to populate Key Vault
- ✅ Not stored in application code
- ✅ OIDC federated access (secure)

**Flow**: `GitHub Secrets → Bicep Parameters → Key Vault → Container Apps`

---

### 3. **Environment Variables** (Runtime)

**Set by Container Apps from Key Vault**:

The Bicep templates automatically:
1. Store secrets in Key Vault (from GitHub Secrets)
2. Reference secrets in Container Apps using `secretRef`
3. Set environment variables from Key Vault secrets

**No manual configuration needed** - handled by infrastructure.

---

### 4. **.env File** (Local Development Only) ⚠️

**For local testing**:

```bash
# .env (gitignored - local development only)
AZURE_FOUNDRY_AGENT_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_FOUNDRY_AGENT_PROJECT=zimax
AZURE_FOUNDRY_AGENT_KEY=<local-dev-key>  # Optional
ELENA_FOUNDRY_AGENT_ID=cf23c3ed0f9d420dbd02c1e95a5b5bb3
USE_FOUNDRY_ELENA=true  # For testing
```

**Why .env**:
- ✅ Local development convenience
- ✅ Not committed to git
- ✅ Overridden by Key Vault in production

---

## Configuration Priority

The application reads configuration in this order:

1. **Key Vault** (if `AZURE_KEYVAULT_URL` set and `ENVIRONMENT != "development"`)
   - Overrides all other sources
   - Production source of truth

2. **Environment Variables** (from Container App `secretRef` or system)
   - Set from Key Vault in production
   - Set from `.env` in local development

3. **Default Values** (from Settings class)
   - Fallback if not set elsewhere

---

## Implementation Status

### ✅ Completed

1. **KeyVaultSettings** (`backend/core/config.py`)
   - Added Foundry secret mappings
   - Automatically loads from Key Vault in production

2. **Bicep Templates**:
   - `infra/modules/keyvault-secrets.bicep` - Stores Foundry secrets
   - `infra/main.bicep` - Accepts Foundry parameters
   - `infra/modules/backend-aca.bicep` - References Foundry secrets

3. **Deployment Workflow** (`.github/workflows/deploy.yml`)
   - Accepts Foundry parameters from GitHub Secrets
   - Passes to Bicep templates

### 📋 Next Steps

1. **Store Secrets in Key Vault**:
   ```bash
   az keyvault secret set --vault-name "staging-env-kv" --name "azure-foundry-agent-endpoint" --value "https://zimax.services.ai.azure.com"
   az keyvault secret set --vault-name "staging-env-kv" --name "azure-foundry-agent-project" --value "zimax"
   az keyvault secret set --vault-name "staging-env-kv" --name "elena-foundry-agent-id" --value "cf23c3ed0f9d420dbd02c1e95a5b5bb3"
   ```

2. **Add GitHub Secrets**:
   - Go to GitHub → Settings → Secrets → Actions
   - Add: `AZURE_FOUNDRY_AGENT_ENDPOINT`, `AZURE_FOUNDRY_AGENT_PROJECT`, `ELENA_FOUNDRY_AGENT_ID`

3. **Deploy Infrastructure**:
   - Next deployment will automatically:
     - Read GitHub Secrets
     - Store in Key Vault (if not already there)
     - Reference in Container Apps
     - Set environment variables

---

## Verification

### Check Key Vault Secrets

```bash
az keyvault secret show \
  --vault-name "staging-env-kv" \
  --name "azure-foundry-agent-endpoint" \
  --query "value" -o tsv

az keyvault secret show \
  --vault-name "staging-env-kv" \
  --name "azure-foundry-agent-project" \
  --query "value" -o tsv

az keyvault secret show \
  --vault-name "staging-env-kv" \
  --name "elena-foundry-agent-id" \
  --query "value" -o tsv
```

### Check Container App Environment Variables

```bash
az containerapp show \
  --name "engram-api" \
  --resource-group "engram-rg" \
  --query "properties.template.containers[0].env" \
  --output table
```

Look for:
- `AZURE_FOUNDRY_AGENT_ENDPOINT` (from Key Vault)
- `AZURE_FOUNDRY_AGENT_PROJECT` (from Key Vault)
- `ELENA_FOUNDRY_AGENT_ID` (from Key Vault)

---

## Summary

**Source of Truth Hierarchy**:

1. **Key Vault** → Production secrets (single source of truth)
2. **GitHub Secrets** → CI/CD deployment parameters
3. **Environment Variables** → Runtime (from Key Vault or .env)
4. **.env Files** → Local development only

**For Your Foundry Configuration**:
- ✅ Store in Key Vault: `azure-foundry-agent-endpoint`, `azure-foundry-agent-project`, `elena-foundry-agent-id`
- ✅ Add to GitHub Secrets for deployment
- ✅ Bicep templates automatically handle the rest
- ✅ Application reads from environment variables (populated from Key Vault)

**Next Action**: Store secrets in Key Vault and add to GitHub Secrets, then deploy.

---

*Last Updated: January 2026*

