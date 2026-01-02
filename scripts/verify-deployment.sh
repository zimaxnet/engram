#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting Deployment Verification...${NC}"

# 1. Check Azure Container App Environment Variables (CORS_ORIGINS)
echo -e "\n1. Checking CORS_ORIGINS configuration..."
CORS_ENV=$(az containerapp show --name staging-env-api --resource-group engram-rg --query "properties.template.containers[0].env[?name=='CORS_ORIGINS'].value" -o tsv)

if [[ $CORS_ENV == *"https://engram.work"* ]]; then
    echo -e "${GREEN}✓ CORS_ORIGINS correct:${NC} $CORS_ENV"
else
    echo -e "${RED}✗ CORS_ORIGINS incorrect:${NC} $CORS_ENV"
    echo "Expected to contain https://engram.work"
    exit 1
fi

# 2. Check Azure Platform Auth (Easy Auth) Status
echo -e "\n2. Checking Platform Auth status (must be DISABLED)..."
AUTH_STATUS=$(az containerapp auth show --name staging-env-api --resource-group engram-rg --query "platform.enabled" -o tsv)

if [[ $AUTH_STATUS == "false" ]]; then
    echo -e "${GREEN}✓ Platform Auth is DISABLED${NC}"
else
    echo -e "${RED}✗ Platform Auth is ENABLED${NC}"
    echo "This blocks OPTIONS requests. Fix with:"
    echo "az containerapp auth update --name staging-env-api --resource-group engram-rg --enabled false --action AllowAnonymous"
    exit 1
fi

# 3. Test OPTIONS Request via Curl
echo -e "\n3. Testing live OPTIONS request..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS https://api.engram.work/api/v1/chat \
  -H "Origin: https://engram.work" \
  -H "Access-Control-Request-Method: POST")

if [[ $HTTP_CODE == "200" ]]; then
    echo -e "${GREEN}✓ OPTIONS request returned 200 OK${NC}"
else
    echo -e "${RED}✗ OPTIONS request returned $HTTP_CODE${NC}"
    echo "Expected 200"
    exit 1
fi

echo -e "\n${GREEN}All verification checks passed! Deployment is valid.${NC}"
