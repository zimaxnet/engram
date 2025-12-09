# GitHub Secrets Setup Guide

This guide will help you set up all required GitHub secrets for the Engram platform CI/CD pipeline.

## Quick Setup (Recommended)

Use the automated setup script:

```bash
./scripts/setup-github-secrets-quick.sh [resource-group] [location]
```

Example:
```bash
./scripts/setup-github-secrets-quick.sh engram-rg eastus
```

This script will:
1. Create an Azure service principal
2. Set all required GitHub secrets
3. Save credentials locally (in `.gitignore`)

## Manual Setup

### Step 1: Create Azure Service Principal

```bash
# Login to Azure
az login

# Set variables
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
RESOURCE_GROUP="engram-rg"
SP_NAME="engram-github-actions"

# Create service principal
az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
  --sdk-auth > azure-credentials.json
```

### Step 2: Get Admin Object ID

```bash
az ad signed-in-user show --query id -o tsv
```

### Step 3: Set GitHub Secrets

#### Option A: Using GitHub CLI

```bash
# Login to GitHub CLI
gh auth login

# Set secrets
gh secret set AZURE_CREDENTIALS --body "$(cat azure-credentials.json)"
gh secret set AZURE_ADMIN_OBJECT_ID --body "$(az ad signed-in-user show --query id -o tsv)"
gh secret set POSTGRES_PASSWORD --body "your-secure-password"
gh secret set AZURE_OPENAI_KEY --body "your-openai-key"  # Optional
gh secret set AZURE_SPEECH_KEY --body "your-speech-key"  # Optional
```

#### Option B: Using GitHub Web UI

1. Go to your repository: `https://github.com/YOUR_ORG/YOUR_REPO`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

| Secret Name | Value |
|------------|-------|
| `AZURE_CREDENTIALS` | Entire JSON from `azure-credentials.json` |
| `AZURE_ADMIN_OBJECT_ID` | Output from `az ad signed-in-user show --query id -o tsv` |
| `POSTGRES_PASSWORD` | Secure password for PostgreSQL |
| `AZURE_OPENAI_KEY` | Your Azure OpenAI API key (optional) |
| `AZURE_SPEECH_KEY` | Your Azure Speech API key (optional) |

## Required Secrets

### 1. AZURE_CREDENTIALS (Required)

Service principal JSON for Azure authentication. Format:
```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "...",
  ...
}
```

### 2. AZURE_ADMIN_OBJECT_ID (Required)

Your Azure AD user object ID. Used for Key Vault access.

### 3. POSTGRES_PASSWORD (Required)

Password for PostgreSQL database. Must be strong (min 8 chars, mixed case, numbers, symbols).

### 4. AZURE_OPENAI_KEY (Optional)

Azure OpenAI API key. Required if you want agent functionality.

### 5. AZURE_SPEECH_KEY (Optional)

Azure Speech Services API key. Required for voice features.

## Verify Secrets

Check that secrets are set:

```bash
gh secret list
```

You should see:
- ✓ AZURE_CREDENTIALS
- ✓ AZURE_ADMIN_OBJECT_ID
- ✓ POSTGRES_PASSWORD
- (Optional) AZURE_OPENAI_KEY
- (Optional) AZURE_SPEECH_KEY

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `azure-credentials.json` to git
- The file is automatically added to `.gitignore`
- Rotate service principal credentials quarterly
- Use environment-specific secrets for staging/production

## Troubleshooting

### "Resource not accessible by integration"

- Ensure service principal has **Contributor** role on resource group
- Verify subscription ID in `AZURE_CREDENTIALS` matches your Azure subscription

### "Key Vault access denied"

- Ensure your user (via `AZURE_ADMIN_OBJECT_ID`) has **Key Vault Administrator** role
- Or grant service principal **Key Vault Secrets User** role

### Service principal already exists

If you get an error that the service principal already exists:

```bash
# Delete existing service principal
az ad sp delete --id "http://engram-github-actions"

# Or use a different name
SP_NAME="engram-github-actions-v2"
```

## Next Steps

After setting secrets:

1. **Verify secrets**: `gh secret list`
2. **Test deployment**: Run the workflow manually from GitHub Actions
3. **Monitor**: Check workflow logs for any errors
4. **Deploy**: Push to `main` branch to trigger automatic deployment

## Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Azure Service Principal Guide](https://docs.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli)
- [Full GitHub Secrets Guide](github-secrets.md)

