---
layout: default
title: Configuration Source of Truth Strategy
parent: Architecture
nav_order: 9
---

# Configuration Source of Truth Strategy

> **Last Updated**: January 2026  
> **Principle**: Key Vault is the single source of truth for production secrets

---

## Configuration Hierarchy

### 1. **Azure Key Vault** (Production Source of Truth) ✅

**Purpose**: Single source of truth for all production secrets and configuration

**When Used**:
- ✅ Production environments
- ✅ Staging/UAT environments
- ✅ Any environment where `AZURE_KEYVAULT_URL` is set and `ENVIRONMENT != "development"`

**Access Method**:
- Managed Identity (user-assigned)
- Role: `Key Vault Secrets User`
- No secrets in code or environment variables

**Secrets Stored**:
- All API keys and passwords
- Connection strings
- Foundry configuration
- Agent IDs

**Location**: `{envName}-kv.vault.azure.net` (e.g., `staging-env-kv.vault.azure.net`)

---

### 2. **GitHub Secrets** (CI/CD Source of Truth) ✅

**Purpose**: Secrets used during deployment to populate Key Vault

**When Used**:
- ✅ GitHub Actions workflows
- ✅ Deployment pipelines
- ✅ Bicep template parameters

**Access Method**:
- GitHub Actions secrets
- OIDC federated service principal
- Scoped to specific workflows

**Secrets Stored**:
- Deployment-time secrets (passed to Bicep)
- Container Registry tokens
- Service principal credentials

**Flow**: `GitHub Secrets → Bicep Parameters → Key Vault → Container Apps`

---

### 3. **Environment Variables** (Runtime) ✅

**Purpose**: Runtime configuration read by application

**When Used**:
- ✅ All environments (production, staging, development)
- ✅ Set from Key Vault secrets (production)
- ✅ Set from .env file (local development)

**Access Method**:
- Container Apps: `secretRef` to Key Vault
- Local Dev: `.env` file (gitignored)

**Source Priority**:
1. Key Vault (if configured and not development)
2. Environment variables (from .env or system)
3. Default values (from Settings class)

---

### 4. **.env Files** (Local Development Only) ⚠️

**Purpose**: Local development convenience

**When Used**:
- ✅ Local development only
- ❌ Never committed to git
- ❌ Never used in production

**Access Method**:
- Pydantic Settings reads `.env` file
- Gitignored (in `.gitignore`)

**Secrets Stored**:
- Local API keys (for testing)
- Local database credentials
- Development-only configuration

---

## Configuration Flow

### Production Flow

```
┌─────────────────────────────────────────────────────────┐
│              Azure Key Vault (Source of Truth)          │
│  - All production secrets                               │
│  - Managed Identity access                              │
│  - RBAC protected                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         Container App (Secret References)                │
│  - secretRef to Key Vault URLs                          │
│  - No secrets in environment variables                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         Application Runtime (Environment Variables)       │
│  - Settings class reads from env vars                    │
│  - Key Vault values override defaults                    │
└─────────────────────────────────────────────────────────┘
```

### Deployment Flow

```
┌─────────────────────────────────────────────────────────┐
│              GitHub Secrets (CI/CD)                      │
│  - Deployment-time secrets                              │
│  - OIDC federated access                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         GitHub Actions Workflow                          │
│  - Reads secrets from GitHub                             │
│  - Passes to Bicep as parameters                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         Bicep Templates                                  │
│  - Receives secrets as parameters                        │
│  - Stores in Key Vault                                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         Azure Key Vault                                  │
│  - Secrets stored via Bicep                              │
│  - Becomes source of truth                               │
└─────────────────────────────────────────────────────────┘
```

---

## Foundry Configuration Strategy

### Current Foundry Settings

Based on your configuration:
- **Endpoint**: `https://zimax.services.ai.azure.com/api/projects/zimax`
- **Project**: `zimax`
- **Region**: `eastus2`
- **Agent ID**: `cf23c3ed0f9d420dbd02c1e95a5b5bb3` (if this is Elena's agent ID)

### Where to Store Foundry Configuration

#### ✅ **Key Vault** (Production)

**Secrets to Store**:
- `azure-foundry-agent-endpoint` → `https://zimax.services.ai.azure.com`
- `azure-foundry-agent-project` → `zimax`
- `azure-foundry-agent-key` → (API key, if using key auth)
- `elena-foundry-agent-id` → `cf23c3ed0f9d420dbd02c1e95a5b5bb3` (if this is Elena's ID)

**Why Key Vault**:
- ✅ Single source of truth
- ✅ Secure storage
- ✅ Managed Identity access
- ✅ No secrets in code
- ✅ Easy rotation

#### ✅ **GitHub Secrets** (CI/CD)

**Secrets for Deployment**:
- `AZURE_FOUNDRY_AGENT_ENDPOINT` → Used in Bicep to populate Key Vault
- `AZURE_FOUNDRY_AGENT_PROJECT` → Used in Bicep to populate Key Vault
- `AZURE_FOUNDRY_AGENT_KEY` → (Optional, if using key auth)

**Why GitHub Secrets**:
- ✅ Used during deployment only
- ✅ Populates Key Vault
- ✅ Not stored in application

#### ⚠️ **.env File** (Local Development Only)

**For Local Testing**:
```bash
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

## Implementation

### Step 1: Store in Key Vault

```bash
# Using Azure CLI
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
```

### Step 2: Update Bicep Templates

Add Foundry secrets to `infra/modules/keyvault-secrets.bicep`:

```bicep
// Foundry Agent Service
@description('Azure AI Foundry Agent Service endpoint')
param azureFoundryAgentEndpoint string = ''

@description('Azure AI Foundry Agent Service project name')
param azureFoundryAgentProject string = ''

@description('Elena Foundry Agent ID')
param elenaFoundryAgentId string = ''

// Store in Key Vault
if (!empty(azureFoundryAgentEndpoint)) {
  resource foundryEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
    name: '${keyVaultName}/azure-foundry-agent-endpoint'
    properties: {
      value: azureFoundryAgentEndpoint
    }
  }
}

if (!empty(azureFoundryAgentProject)) {
  resource foundryProjectSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
    name: '${keyVaultName}/azure-foundry-agent-project'
    properties: {
      value: azureFoundryAgentProject
    }
  }
}

if (!empty(elenaFoundryAgentId)) {
  resource elenaAgentIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
    name: '${keyVaultName}/elena-foundry-agent-id'
    properties: {
      value: elenaFoundryAgentId
    }
  }
}
```

### Step 3: Update Container App Configuration

Add secret references in `infra/modules/backend-aca.bicep`:

```bicep
secrets: [
  // ... existing secrets ...
  {
    name: 'azure-foundry-agent-endpoint'
    keyVaultUrl: '${keyVaultUri}secrets/azure-foundry-agent-endpoint'
    identity: identityResourceId
  }
  {
    name: 'azure-foundry-agent-project'
    keyVaultUrl: '${keyVaultUri}secrets/azure-foundry-agent-project'
    identity: identityResourceId
  }
  {
    name: 'elena-foundry-agent-id'
    keyVaultUrl: '${keyVaultUri}secrets/elena-foundry-agent-id'
    identity: identityResourceId
  }
]

env: [
  // ... existing env vars ...
  {
    name: 'AZURE_FOUNDRY_AGENT_ENDPOINT'
    secretRef: 'azure-foundry-agent-endpoint'
  }
  {
    name: 'AZURE_FOUNDRY_AGENT_PROJECT'
    secretRef: 'azure-foundry-agent-project'
  }
  {
    name: 'ELENA_FOUNDRY_AGENT_ID'
    secretRef: 'elena-foundry-agent-id'
  }
]
```

### Step 4: Update GitHub Secrets

Add to GitHub repository secrets:

- `AZURE_FOUNDRY_AGENT_ENDPOINT` → `https://zimax.services.ai.azure.com`
- `AZURE_FOUNDRY_AGENT_PROJECT` → `zimax`
- `ELENA_FOUNDRY_AGENT_ID` → `cf23c3ed0f9d420dbd02c1e95a5b5bb3`

---

## Configuration Priority

The application reads configuration in this order:

1. **Key Vault** (if `AZURE_KEYVAULT_URL` set and `ENVIRONMENT != "development"`)
   - Overrides all other sources
   - Production source of truth

2. **Environment Variables** (from Container App or system)
   - Set from Key Vault `secretRef` in production
   - Set from `.env` file in local development

3. **Default Values** (from Settings class)
   - Fallback if not set elsewhere
   - Non-sensitive defaults only

---

## Best Practices

### ✅ DO

- ✅ Store all production secrets in Key Vault
- ✅ Use Managed Identity for Key Vault access
- ✅ Reference secrets using `secretRef` in Container Apps
- ✅ Use GitHub Secrets for deployment-time values
- ✅ Use .env files for local development only
- ✅ Document secret names and purposes
- ✅ Rotate secrets regularly (90 days)

### ❌ DON'T

- ❌ Hardcode secrets in code
- ❌ Commit secrets to version control
- ❌ Store secrets in environment variables directly (use `secretRef`)
- ❌ Use .env files in production
- ❌ Log secret values
- ❌ Share secrets via email or chat

---

## Secret Naming Convention

### Key Vault Secret Names

Use kebab-case with descriptive names:

- `azure-foundry-agent-endpoint`
- `azure-foundry-agent-project`
- `azure-foundry-agent-key`
- `elena-foundry-agent-id`

### Environment Variable Names

Use UPPER_SNAKE_CASE matching Settings class:

- `AZURE_FOUNDRY_AGENT_ENDPOINT`
- `AZURE_FOUNDRY_AGENT_PROJECT`
- `AZURE_FOUNDRY_AGENT_KEY`
- `ELENA_FOUNDRY_AGENT_ID`

---

## Migration Checklist

For Foundry configuration:

- [ ] Store secrets in Key Vault
- [ ] Update Bicep templates to accept Foundry parameters
- [ ] Update Container App configuration with secret references
- [ ] Add GitHub Secrets for deployment
- [ ] Update `KeyVaultSettings.apply_to_settings()` (already done)
- [ ] Test in staging environment
- [ ] Document secret names and purposes
- [ ] Update deployment documentation

---

## Summary

**Source of Truth Hierarchy**:

1. **Key Vault** → Production secrets (single source of truth)
2. **GitHub Secrets** → CI/CD deployment parameters
3. **Environment Variables** → Runtime configuration (from Key Vault or .env)
4. **.env Files** → Local development only

**For Foundry**:
- ✅ Store in Key Vault: `azure-foundry-agent-endpoint`, `azure-foundry-agent-project`, `elena-foundry-agent-id`
- ✅ Add to GitHub Secrets for deployment
- ✅ Use `secretRef` in Container Apps
- ✅ Application reads from environment variables (populated from Key Vault)

---

*Last Updated: January 2026*

