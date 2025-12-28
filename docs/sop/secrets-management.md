# Secrets Management SOP

## Overview

All secrets in Engram are managed through **Azure Key Vault** and **GitHub Secrets**. No secrets are hardcoded in the codebase or committed to version control.

## Secret Sources

### 1. Azure Key Vault (Primary)

All production secrets are stored in Azure Key Vault and referenced by Container Apps using Managed Identity.

**Key Vault Location:**
- Resource Group: `engram-rg`
- Key Vault Name: `{envName}-kv` (e.g., `staging-env-kv`)

**Required Secrets:**

| Secret Name | Description | Used By |
|------------|-------------|---------|
| `zep-api-key` | Zep Memory Service API key | Backend, Worker |
| `azure-ai-key` | Azure AI Services API key (APIM subscription key) | Backend, Worker, Zep |
| `postgres-password` | PostgreSQL admin password | Backend, Worker, Zep, Temporal |
| `voicelive-api-key` | Azure VoiceLive API key (optional) | Backend |
| `anthropic-api-key` | Anthropic Claude API key (optional, for Sage) | Backend |
| `gemini-api-key` | Google Gemini API key (optional, for Sage) | Backend |

### 2. GitHub Secrets (CI/CD)

GitHub Secrets are used during deployment to pass values to Bicep templates.

**Required GitHub Secrets:**

| Secret Name | Description | Used In |
|------------|-------------|---------|
| `ZEP_API_KEY` | Zep API key (stored in Key Vault during deployment) | `.github/workflows/deploy.yml` |
| `AZURE_AI_ENDPOINT` | Azure AI endpoint URL | `.github/workflows/deploy.yml` |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key (alternative to APIM key) | `.github/workflows/deploy.yml` |
| `POSTGRES_PASSWORD` | PostgreSQL password (stored in Key Vault) | `.github/workflows/deploy.yml` |
| `CR_PAT` | GitHub Container Registry Personal Access Token | `.github/workflows/deploy.yml` |

## Secret Flow

### Deployment Flow

```
GitHub Secrets → Bicep Parameters → Key Vault → Container App Secrets → Environment Variables
```

1. **GitHub Actions** reads secrets from GitHub Secrets
2. **Bicep templates** receive secrets as parameters
3. **Key Vault** stores secrets (via `modules/keyvault-secrets.bicep`)
4. **Container Apps** reference Key Vault secrets using Managed Identity
5. **Backend/Worker** read secrets from environment variables

### Runtime Flow

```
Container App → Managed Identity → Key Vault → Environment Variable → Application Code
```

1. **Container App** uses Managed Identity to access Key Vault
2. **Key Vault** returns secret value
3. **Environment Variable** is set in container
4. **Application Code** reads from environment variable (via `backend/core/config.py`)

## Configuration Files

### Backend Configuration (`backend/core/config.py`)

All secrets are read from environment variables:

```python
class Settings(BaseSettings):
    zep_api_key: Optional[str] = Field(None, alias="ZEP_API_KEY")
    azure_ai_key: Optional[str] = Field(None, alias="AZURE_AI_KEY")
    postgres_password: str = Field("password", alias="POSTGRES_PASSWORD")
    # ... other settings
```

### Bicep Templates

Secrets are referenced from Key Vault:

```bicep
// infra/modules/backend-aca.bicep
secrets: [
  {
    name: 'zep-api-key'
    keyVaultUrl: '${keyVaultUri}secrets/zep-api-key'
    identity: identityResourceId
  }
  // ...
]

env: [
  {
    name: 'ZEP_API_KEY'
    secretRef: 'zep-api-key'
  }
  // ...
]
```

## Security Best Practices

### ✅ DO

- ✅ Store all secrets in Azure Key Vault
- ✅ Use Managed Identity for Key Vault access
- ✅ Reference secrets using `secretRef` in Container Apps
- ✅ Read secrets from environment variables in code
- ✅ Use GitHub Secrets for CI/CD deployment parameters
- ✅ Rotate secrets regularly
- ✅ Use separate secrets for different environments

### ❌ DON'T

- ❌ Hardcode secrets in code
- ❌ Commit secrets to version control
- ❌ Store secrets in `.env` files (local dev only)
- ❌ Log secret values
- ❌ Pass secrets as command-line arguments
- ❌ Use the same secrets across environments

## Verifying Secret Configuration

### Check Key Vault Secrets

```bash
# List all secrets
az keyvault secret list --vault-name {key-vault-name} --query "[].name" --output table

# Check specific secret exists
az keyvault secret show --vault-name {key-vault-name} --name zep-api-key --query "name" --output tsv
```

### Check Container App Environment Variables

```bash
# List environment variables (secretRef values are masked)
az containerapp show \
  --name {app-name} \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env" \
  --output table
```

### Check GitHub Secrets

GitHub Secrets can only be viewed in the GitHub repository settings:
1. Go to: `Settings` → `Secrets and variables` → `Actions`
2. Verify required secrets are present

## Troubleshooting

### Secret Not Found

**Error:** `SecretNotFound` or `401 Unauthorized`

**Solution:**
1. Verify secret exists in Key Vault
2. Check Managed Identity has `Key Vault Secrets User` role
3. Check Container App has correct Managed Identity assigned

### Secret Not Accessible

**Error:** Application can't read secret value

**Solution:**
1. Verify `secretRef` is correctly set in Container App
2. Check Managed Identity has access to Key Vault
3. Verify secret name matches exactly (case-sensitive)

### Secret Outdated

**Error:** Application using old secret value

**Solution:**
1. Update secret in Key Vault
2. Restart Container App to pick up new value
3. Or update secret reference to force refresh

## Related Documentation

- [Azure Key Vault Documentation](https://docs.microsoft.com/azure/key-vault/)
- [Container Apps Managed Identity](https://docs.microsoft.com/azure/container-apps/managed-identity)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

