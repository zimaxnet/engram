# GitHub Secrets Configuration Guide

This document outlines all required GitHub secrets for CI/CD deployment of the Engram platform.

## Required Secrets

### Azure Authentication

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AZURE_CREDENTIALS` | Service principal JSON for Azure authentication | See [Creating Service Principal](#creating-service-principal) |

### Azure Resources

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `AZURE_KEY_VAULT_URL` | Key Vault URI (e.g., `https://engram-env-kv.vault.azure.net/`) | From Azure Portal or Bicep output |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web Apps deployment token | From Azure Portal → Static Web App → Manage deployment token |
| `API_URL` | Backend API URL (e.g., `https://engram-api.azurecontainerapps.io`) | From Container App FQDN |
| `WS_URL` | WebSocket URL (same as API_URL but `ws://` or `wss://`) | From Container App FQDN |
| `TEMPORAL_HOST` | Temporal gRPC endpoint (e.g., `temporal-server.engram-env-aca.region.azurecontainerapps.io:7233`) | From Temporal Container App |

### Optional Notifications

| Secret Name | Description | How to Get |
|------------|-------------|------------|
| `SLACK_WEBHOOK_URL` | Slack webhook for deployment notifications | Create Slack Incoming Webhook |

## Creating Service Principal

### Using Azure CLI

```bash
# Login to Azure
az login

# Set variables
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
RESOURCE_GROUP="engram-rg"
SP_NAME="engram-github-actions"

# Create service principal with contributor role
az ad sp create-for-rbac \
  --name $SP_NAME \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth

# Output will be JSON like:
# {
#   "clientId": "...",
#   "clientSecret": "...",
#   "subscriptionId": "...",
#   "tenantId": "...",
#   ...
# }
```

### Using Azure Portal

1. Go to **Azure Active Directory** → **App registrations**
2. Click **New registration**
3. Name: `engram-github-actions`
4. Click **Register**
5. Go to **Certificates & secrets** → **New client secret**
6. Copy the **Value** (this is your `clientSecret`)
7. Copy the **Application (client) ID** (this is your `clientId`)
8. Go to **Subscriptions** → Select your subscription → **Access control (IAM)**
9. Click **Add** → **Add role assignment**
10. Role: **Contributor**
11. Assign access to: **Service principal**
12. Select your app registration

### Format for GitHub Secret

The `AZURE_CREDENTIALS` secret should be the entire JSON output from `az ad sp create-for-rbac`:

```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

## Setting Secrets in GitHub

### Via GitHub Web UI

1. Go to your repository: `https://github.com/zimaxnet/engram`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name and value
5. Click **Add secret**

### Via GitHub CLI

```bash
# Install GitHub CLI if needed
# brew install gh (macOS)
# or download from https://cli.github.com

# Login
gh auth login

# Set secrets
gh secret set AZURE_CREDENTIALS --body "$(cat azure-credentials.json)"
gh secret set AZURE_KEY_VAULT_URL --body "https://engram-env-kv.vault.azure.net/"
gh secret set API_URL --body "https://engram-api.azurecontainerapps.io"
gh secret set WS_URL --body "wss://engram-api.azurecontainerapps.io"
gh secret set TEMPORAL_HOST --body "temporal-server.engram-env-aca.eastus.azurecontainerapps.io:7233"
```

## Environment-Specific Secrets

For staging/production environments, you can set secrets at the environment level:

1. Go to **Settings** → **Environments**
2. Create environments: `staging`, `production`
3. Add secrets to each environment
4. The workflow will use environment-specific secrets when `environment: staging` or `environment: production` is specified

## Verifying Secrets

After setting secrets, verify they're accessible:

```bash
# Check if secrets are set (names only, not values)
gh secret list
```

## Security Best Practices

1. **Never commit secrets to code** - Always use GitHub Secrets
2. **Rotate secrets regularly** - Update service principal passwords quarterly
3. **Use least privilege** - Service principal should only have access to required resources
4. **Use environment-specific secrets** - Separate staging and production credentials
5. **Audit access** - Regularly review who has access to secrets

## Troubleshooting

### "Resource not accessible by integration"

- Ensure service principal has Contributor role on the resource group
- Check that `AZURE_CREDENTIALS` JSON is valid
- Verify subscription ID matches

### "Key Vault access denied"

- Ensure service principal has "Key Vault Secrets User" role on Key Vault
- Check Key Vault access policies (if using access policies instead of RBAC)

### "Container App deployment failed"

- Verify Container Apps Environment exists
- Check that image is pushed to container registry
- Ensure service principal has "Contributor" role on Container Apps

## Next Steps

After setting all secrets:

1. Run the deployment workflow manually via GitHub Actions
2. Monitor the workflow logs for any errors
3. Verify resources are created in Azure Portal
4. Test the deployed endpoints

