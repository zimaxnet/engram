#!/bin/bash
# deploy-config-only.sh - Update Azure Container App environment variables without rebuilding images
# Usage: ./scripts/deploy-config-only.sh [KEY=VALUE ...]
# Example: ./scripts/deploy-config-only.sh AUTH_REQUIRED=false ENVIRONMENT=staging

set -e

RESOURCE_GROUP="engram-rg"
CONTAINER_APPS=("staging-env-api" "staging-env-worker")

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Config-Only Deployment${NC}"
echo "================================"
echo ""

# Check if any arguments provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 KEY=VALUE [KEY=VALUE ...]${NC}"
    echo ""
    echo "Common configuration options:"
    echo "  AUTH_REQUIRED=false     - Disable authentication (POC mode)"
    echo "  AUTH_REQUIRED=true      - Enable authentication"
    echo "  ENVIRONMENT=staging     - Set environment"
    echo "  CORS_ORIGINS='[...]'    - Set CORS origins"
    echo ""
    echo "Example:"
    echo "  $0 AUTH_REQUIRED=false"
    exit 1
fi

# Build env-vars string
ENV_VARS="$@"

echo -e "📝 Environment variables to update: ${YELLOW}${ENV_VARS}${NC}"
echo ""

# Check Azure CLI login
if ! az account show &>/dev/null; then
    echo -e "${RED}❌ Not logged in to Azure CLI. Run 'az login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Azure CLI authenticated"
echo ""

# Update each container app
for APP in "${CONTAINER_APPS[@]}"; do
    echo -e "📦 Updating ${YELLOW}${APP}${NC}..."
    
    if az containerapp update \
        --name "$APP" \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars $ENV_VARS \
        --output none 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} ${APP} updated"
    else
        echo -e "   ${RED}✗${NC} Failed to update ${APP}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}✅ Configuration updated successfully!${NC}"
echo ""
echo "Note: Containers will restart automatically with new config."
echo "This takes ~30-60 seconds. Check status with:"
echo "  az containerapp list --resource-group $RESOURCE_GROUP --query \"[].{name:name,running:properties.runningStatus}\" -o table"
