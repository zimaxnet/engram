#!/bin/bash
# Quick setup script for GitHub secrets (minimal prompts)

set -e

echo "=========================================="
echo "Engram Platform - Quick GitHub Secrets Setup"
echo "=========================================="
echo ""

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI not installed. Install from: https://aka.ms/InstallAzureCLI"
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI not installed. Install from: https://cli.github.com"
    exit 1
fi

# Check login status
if ! az account show &> /dev/null; then
    echo "Logging into Azure..."
    az login
fi

if ! gh auth status &> /dev/null; then
    echo "Logging into GitHub..."
    gh auth login
fi

# Get Azure info
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
RESOURCE_GROUP=${1:-engram-rg}
SP_NAME="engram-github-actions"

echo "Subscription: $(az account show --query name -o tsv)"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Create or verify resource group
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    read -p "Resource group doesn't exist. Create it? (y/n): " CREATE_RG
    if [[ $CREATE_RG == "y" ]]; then
        LOCATION=${2:-eastus}
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    else
        exit 1
    fi
fi

# Create service principal
echo "Creating service principal..."
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    --sdk-auth)

# Save credentials
echo "$SP_OUTPUT" > azure-credentials.json
chmod 600 azure-credentials.json

# Get admin object ID
ADMIN_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)

# Set GitHub secrets
echo ""
echo "Setting GitHub secrets..."

echo "$SP_OUTPUT" | gh secret set AZURE_CREDENTIALS
echo "$ADMIN_OBJECT_ID" | gh secret set AZURE_ADMIN_OBJECT_ID

# Prompt for PostgreSQL password
read -sp "Enter PostgreSQL password: " POSTGRES_PASSWORD
echo ""
echo "$POSTGRES_PASSWORD" | gh secret set POSTGRES_PASSWORD

# Optional: Azure OpenAI key
read -p "Enter Azure OpenAI key (optional, press Enter to skip): " OPENAI_KEY
if [ -n "$OPENAI_KEY" ]; then
    echo "$OPENAI_KEY" | gh secret set AZURE_OPENAI_KEY
fi

# Optional: Azure Speech key
read -p "Enter Azure Speech key (optional, press Enter to skip): " SPEECH_KEY
if [ -n "$SPEECH_KEY" ]; then
    echo "$SPEECH_KEY" | gh secret set AZURE_SPEECH_KEY
fi

# Add to .gitignore
if [ -f .gitignore ]; then
    if ! grep -q "azure-credentials.json" .gitignore; then
        echo "azure-credentials.json" >> .gitignore
    fi
else
    echo "azure-credentials.json" > .gitignore
fi

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Secrets set:"
echo "  ✓ AZURE_CREDENTIALS"
echo "  ✓ AZURE_ADMIN_OBJECT_ID"
echo "  ✓ POSTGRES_PASSWORD"
[ -n "$OPENAI_KEY" ] && echo "  ✓ AZURE_OPENAI_KEY"
[ -n "$SPEECH_KEY" ] && echo "  ✓ AZURE_SPEECH_KEY"
echo ""
echo "⚠️  azure-credentials.json created - DO NOT COMMIT"
echo ""
echo "Next steps:"
echo "  1. Verify secrets: gh secret list"
echo "  2. Run deployment workflow"
echo ""

