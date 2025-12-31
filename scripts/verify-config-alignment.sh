#!/bin/bash
# Verify Configuration Alignment Across All Sources
# This script checks that configuration is aligned between:
# - Azure Container Apps environment variables
# - Azure Key Vault secrets
# - Expected values

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Configuration Alignment Verification"
echo "=========================================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-zimax-ai}"
CONTAINER_APP="${CONTAINER_APP:-staging-env-api}"
KEY_VAULT="${KEY_VAULT:-models-playground-1130-kv}"  # Adjust based on your env

echo "Resource Group: $RESOURCE_GROUP"
echo "Container App: $CONTAINER_APP"
echo "Key Vault: $KEY_VAULT"
echo ""

# Expected values
EXPECTED_ENDPOINT="https://zimax-gw.azure-api.net/zimax/openai/v1/"
EXPECTED_DEPLOYMENT="gpt-5.1-chat"
EXPECTED_API_VERSION="2024-10-01-preview"
EXPECTED_MODEL_ROUTER=""  # Empty = disabled

echo "Expected Configuration:"
echo "  AZURE_AI_ENDPOINT: $EXPECTED_ENDPOINT"
echo "  AZURE_AI_DEPLOYMENT: $EXPECTED_DEPLOYMENT"
echo "  AZURE_AI_API_VERSION: $EXPECTED_API_VERSION"
echo "  AZURE_AI_MODEL_ROUTER: (empty/not set)"
echo ""

# Check Container App environment variables
echo "=========================================="
echo "1. Checking Azure Container App Environment Variables"
echo "=========================================="

ENV_VARS=$(az containerapp show \
    --name "$CONTAINER_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.template.containers[0].env" \
    --output json 2>/dev/null || echo "[]")

if [ "$ENV_VARS" = "[]" ] || [ -z "$ENV_VARS" ]; then
    echo -e "${RED}❌ Failed to retrieve Container App environment variables${NC}"
    echo "   Make sure the Container App exists and you have access."
    exit 1
fi

# Extract values
ACTUAL_ENDPOINT=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="AZURE_AI_ENDPOINT") | .value // .secretRef // "NOT_SET"')
ACTUAL_DEPLOYMENT=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="AZURE_AI_DEPLOYMENT") | .value // .secretRef // "NOT_SET"')
ACTUAL_API_VERSION=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="AZURE_AI_API_VERSION") | .value // .secretRef // "NOT_SET"')
ACTUAL_MODEL_ROUTER=$(echo "$ENV_VARS" | jq -r '.[] | select(.name=="AZURE_AI_MODEL_ROUTER") | .value // .secretRef // "NOT_SET"')

echo "Actual Configuration:"
echo "  AZURE_AI_ENDPOINT: $ACTUAL_ENDPOINT"
echo "  AZURE_AI_DEPLOYMENT: $ACTUAL_DEPLOYMENT"
echo "  AZURE_AI_API_VERSION: $ACTUAL_API_VERSION"
echo "  AZURE_AI_MODEL_ROUTER: $ACTUAL_MODEL_ROUTER"
echo ""

# Verify endpoint
if [ "$ACTUAL_ENDPOINT" = "$EXPECTED_ENDPOINT" ]; then
    echo -e "${GREEN}✅ AZURE_AI_ENDPOINT matches expected value${NC}"
else
    echo -e "${RED}❌ AZURE_AI_ENDPOINT mismatch!${NC}"
    echo "   Expected: $EXPECTED_ENDPOINT"
    echo "   Actual: $ACTUAL_ENDPOINT"
    echo "   ⚠️  Endpoint MUST include '/openai/v1/' for OpenAI SDK format"
fi

# Verify deployment
if [ "$ACTUAL_DEPLOYMENT" = "$EXPECTED_DEPLOYMENT" ]; then
    echo -e "${GREEN}✅ AZURE_AI_DEPLOYMENT matches expected value${NC}"
else
    echo -e "${YELLOW}⚠️  AZURE_AI_DEPLOYMENT mismatch${NC}"
    echo "   Expected: $EXPECTED_DEPLOYMENT"
    echo "   Actual: $ACTUAL_DEPLOYMENT"
fi

# Verify API version
if [ "$ACTUAL_API_VERSION" = "$EXPECTED_API_VERSION" ]; then
    echo -e "${GREEN}✅ AZURE_AI_API_VERSION matches expected value${NC}"
else
    echo -e "${YELLOW}⚠️  AZURE_AI_API_VERSION mismatch${NC}"
    echo "   Expected: $EXPECTED_API_VERSION"
    echo "   Actual: $ACTUAL_API_VERSION"
fi

# Verify model router is disabled
if [ "$ACTUAL_MODEL_ROUTER" = "NOT_SET" ] || [ -z "$ACTUAL_MODEL_ROUTER" ] || [ "$ACTUAL_MODEL_ROUTER" = '""' ]; then
    echo -e "${GREEN}✅ AZURE_AI_MODEL_ROUTER is disabled (empty/not set)${NC}"
else
    echo -e "${RED}❌ AZURE_AI_MODEL_ROUTER is set! Model Router is active.${NC}"
    echo "   Value: $ACTUAL_MODEL_ROUTER"
    echo "   ⚠️  To use direct model, delete this variable or set to empty string"
fi

echo ""

# Check Key Vault secret
echo "=========================================="
echo "2. Checking Azure Key Vault Secret"
echo "=========================================="

if az keyvault secret show \
    --vault-name "$KEY_VAULT" \
    --name "azure-ai-key" \
    --query "value" \
    --output tsv &> /dev/null; then
    echo -e "${GREEN}✅ Key Vault secret 'azure-ai-key' exists${NC}"
    SECRET_VALUE=$(az keyvault secret show \
        --vault-name "$KEY_VAULT" \
        --name "azure-ai-key" \
        --query "value" \
        --output tsv)
    if [ -n "$SECRET_VALUE" ]; then
        echo -e "${GREEN}✅ Secret has a value (length: ${#SECRET_VALUE} characters)${NC}"
    else
        echo -e "${RED}❌ Secret exists but is empty${NC}"
    fi
else
    echo -e "${RED}❌ Key Vault secret 'azure-ai-key' not found${NC}"
    echo "   Vault: $KEY_VAULT"
    echo "   ⚠️  Create the secret: az keyvault secret set --vault-name $KEY_VAULT --name azure-ai-key --value <your-key>"
fi

echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "To fix any issues:"
echo "1. Update Container App environment variables in Azure Portal"
echo "2. Ensure AZURE_AI_ENDPOINT includes '/openai/v1/'"
echo "3. Set AZURE_AI_MODEL_ROUTER to empty or delete it"
echo "4. Verify Key Vault secret 'azure-ai-key' exists"
echo ""
echo "See: docs/configuration/config-alignment.md for details"

