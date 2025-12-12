#!/bin/bash
# Setup GitHub Secrets for Engram Platform
# This script helps you create Azure service principal and set GitHub secrets

set -e

echo "=========================================="
echo "Engram Platform - GitHub Secrets Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed.${NC}"
    echo "Install it from: https://aka.ms/InstallAzureCLI"
    exit 1
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}Warning: GitHub CLI is not installed.${NC}"
    echo "You can install it from: https://cli.github.com"
    echo "Or set secrets manually via GitHub web UI"
    USE_GH_CLI=false
else
    USE_GH_CLI=true
    echo -e "${GREEN}GitHub CLI found. Will use it to set secrets.${NC}"
fi

# Check if logged into Azure
echo "Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}Not logged into Azure. Logging in...${NC}"
    az login
fi

# Get current Azure subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}Using Azure subscription: ${SUBSCRIPTION_NAME} (${SUBSCRIPTION_ID})${NC}"
echo ""

# Prompt for resource group
read -p "Enter Azure resource group name [engram-rg]: " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-engram-rg}

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    read -p "Resource group '$RESOURCE_GROUP' doesn't exist. Create it? (y/n): " CREATE_RG
    if [[ $CREATE_RG == "y" ]]; then
        read -p "Enter Azure location [eastus]: " LOCATION
        LOCATION=${LOCATION:-eastus}
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        echo -e "${GREEN}Resource group created.${NC}"
    else
        echo -e "${RED}Exiting. Please create the resource group first.${NC}"
        exit 1
    fi
fi

# Prompt for service principal name
read -p "Enter service principal name [engram-github-actions]: " SP_NAME
SP_NAME=${SP_NAME:-engram-github-actions}

echo ""
echo "Creating Azure service principal..."
echo "This will create a service principal with Contributor role on the resource group."

# Create service principal
SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" \
    --sdk-auth)

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create service principal.${NC}"
    exit 1
fi

echo -e "${GREEN}Service principal created successfully!${NC}"
echo ""

# Extract values from JSON
CLIENT_ID=$(echo "$SP_OUTPUT" | grep -o '"clientId": "[^"]*"' | cut -d'"' -f4)
CLIENT_SECRET=$(echo "$SP_OUTPUT" | grep -o '"clientSecret": "[^"]*"' | cut -d'"' -f4)
TENANT_ID=$(echo "$SP_OUTPUT" | grep -o '"tenantId": "[^"]*"' | cut -d'"' -f4)

# Save to file for reference (but don't commit it!)
echo "$SP_OUTPUT" > azure-credentials.json
chmod 600 azure-credentials.json
echo -e "${YELLOW}Service principal credentials saved to azure-credentials.json (DO NOT COMMIT THIS FILE)${NC}"
echo ""

# Get admin object ID (current user)
ADMIN_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
echo -e "${GREEN}Admin Object ID: ${ADMIN_OBJECT_ID}${NC}"
echo ""

# Prompt for GitHub repository
read -p "Enter GitHub repository (format: owner/repo) [zimaxnet/engram]: " GITHUB_REPO
GITHUB_REPO=${GITHUB_REPO:-zimaxnet/engram}

# Check if GitHub CLI is authenticated
if [ "$USE_GH_CLI" = true ]; then
    if ! gh auth status &> /dev/null; then
        echo -e "${YELLOW}GitHub CLI not authenticated. Logging in...${NC}"
        gh auth login
    fi
    
    # Verify we're in the right repo
    CURRENT_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [ "$CURRENT_REPO" != "$GITHUB_REPO" ]; then
        echo -e "${YELLOW}Current directory is not in repo $GITHUB_REPO${NC}"
        read -p "Continue anyway? (y/n): " CONTINUE
        if [[ $CONTINUE != "y" ]]; then
            exit 1
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Setting GitHub Secrets"
echo "=========================================="
echo ""

# Function to set secret via GitHub CLI or show instructions
set_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2
    local DESCRIPTION=$3
    
    if [ "$USE_GH_CLI" = true ]; then
        echo "$SECRET_VALUE" | gh secret set "$SECRET_NAME"
        echo -e "${GREEN}✓ Set ${SECRET_NAME}${NC}"
    else
        echo -e "${YELLOW}→ ${SECRET_NAME}: ${DESCRIPTION}${NC}"
        echo "   Value: ${SECRET_VALUE:0:20}..."
    fi
}

# Set AZURE_CREDENTIALS
if [ "$USE_GH_CLI" = true ]; then
    echo "$SP_OUTPUT" | gh secret set AZURE_CREDENTIALS
    echo -e "${GREEN}✓ Set AZURE_CREDENTIALS${NC}"
else
    echo -e "${YELLOW}→ AZURE_CREDENTIALS: Service principal JSON${NC}"
    echo "   Set this in GitHub: Settings → Secrets and variables → Actions → New repository secret"
    echo "   Value: (see azure-credentials.json)"
fi

# Set AZURE_ADMIN_OBJECT_ID
if [ "$USE_GH_CLI" = true ]; then
    echo "$ADMIN_OBJECT_ID" | gh secret set AZURE_ADMIN_OBJECT_ID
    echo -e "${GREEN}✓ Set AZURE_ADMIN_OBJECT_ID${NC}"
else
    echo -e "${YELLOW}→ AZURE_ADMIN_OBJECT_ID: ${ADMIN_OBJECT_ID}${NC}"
fi

# Set POSTGRES_PASSWORD (prompt user)
echo ""
read -sp "Enter PostgreSQL password for deployment: " POSTGRES_PASSWORD
echo ""
if [ "$USE_GH_CLI" = true ]; then
    echo "$POSTGRES_PASSWORD" | gh secret set POSTGRES_PASSWORD
    echo -e "${GREEN}✓ Set POSTGRES_PASSWORD${NC}"
else
    echo -e "${YELLOW}→ POSTGRES_PASSWORD: (hidden)${NC}"
fi

# Optional secrets
echo ""
echo "Optional secrets (press Enter to skip):"
echo ""

# Azure AI Foundry Key (optional override)
read -p "Enter Azure AI API key (optional): " OPENAI_KEY
if [ -n "$OPENAI_KEY" ]; then
    if [ "$USE_GH_CLI" = true ]; then
        echo "$OPENAI_KEY" | gh secret set AZURE_AI_KEY
        echo -e "${GREEN}✓ Set AZURE_AI_KEY${NC}"
    else
        echo -e "${YELLOW}→ AZURE_AI_KEY: (set manually)${NC}"
    fi
fi

# Static Web Apps token (optional, will be set after first deployment)
echo ""
echo -e "${YELLOW}Note: AZURE_STATIC_WEB_APPS_API_TOKEN will be set after first deployment${NC}"
echo "   Get it from: Azure Portal → Static Web App → Manage deployment token"

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}✓ Service principal created: ${SP_NAME}${NC}"
echo -e "${GREEN}✓ Resource group: ${RESOURCE_GROUP}${NC}"
echo -e "${GREEN}✓ Subscription: ${SUBSCRIPTION_NAME}${NC}"
echo ""

if [ "$USE_GH_CLI" = true ]; then
    echo -e "${GREEN}All secrets have been set in GitHub!${NC}"
else
    echo -e "${YELLOW}Please set the following secrets manually in GitHub:${NC}"
    echo "  1. Go to: https://github.com/${GITHUB_REPO}/settings/secrets/actions"
    echo "  2. Click 'New repository secret'"
    echo "  3. Set each secret from the list above"
    echo ""
    echo "Required secrets:"
    echo "  - AZURE_CREDENTIALS (from azure-credentials.json)"
    echo "  - AZURE_ADMIN_OBJECT_ID: ${ADMIN_OBJECT_ID}"
    echo "  - POSTGRES_PASSWORD: (the password you entered)"
fi

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "  - azure-credentials.json contains sensitive data. DO NOT COMMIT IT!"
echo "  - Add it to .gitignore if not already there"
echo "  - Keep it secure and delete it when no longer needed"
echo ""

# Check if .gitignore exists and contains azure-credentials.json
if [ -f .gitignore ]; then
    if ! grep -q "azure-credentials.json" .gitignore; then
        echo "azure-credentials.json" >> .gitignore
        echo -e "${GREEN}Added azure-credentials.json to .gitignore${NC}"
    fi
else
    echo "azure-credentials.json" > .gitignore
    echo -e "${GREEN}Created .gitignore with azure-credentials.json${NC}"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""

