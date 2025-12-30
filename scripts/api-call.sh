#!/bin/bash
# api-call.sh - Make authenticated API calls to Engram using Azure AD
# Usage: ./scripts/api-call.sh <method> <endpoint> [json-data]
# Examples:
#   ./scripts/api-call.sh GET /api/v1/agents
#   ./scripts/api-call.sh POST /api/v1/story/create '{"topic":"Test Story"}'
#   ./scripts/api-call.sh GET /health

set -e

API_BASE_URL="${ENGRAM_API_URL:-https://api.engram.work}"
# App registration for the API (audience)
API_APP_ID="${ENGRAM_API_APP_ID:-317f549d-67bb-4f73-90a3-ac0ebf95a420}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
METHOD="${1:-GET}"
ENDPOINT="${2:-/health}"
DATA="${3:-}"

if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 <method> <endpoint> [json-data]"
    echo ""
    echo "Examples:"
    echo "  $0 GET /api/v1/agents"
    echo "  $0 POST /api/v1/story/create '{\"topic\":\"My Story\"}'"
    echo "  $0 GET /health"
    echo ""
    echo "Environment variables:"
    echo "  ENGRAM_API_URL     - API base URL (default: https://api.engram.work)"
    echo "  ENGRAM_API_APP_ID  - API app registration ID"
    exit 0
fi

# Get access token using Azure CLI
echo -e "${YELLOW}🔐 Getting access token from Azure AD...${NC}"

# Try to get token for the API app
TOKEN=$(az account get-access-token --resource "api://${API_APP_ID}" --query accessToken -o tsv 2>/dev/null || true)

if [ -z "$TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Token for API resource not available, trying MS Graph scope...${NC}"
    # Fallback: get token with default scope (will work for user identity)
    TOKEN=$(az account get-access-token --query accessToken -o tsv 2>/dev/null || true)
fi

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get access token. Run 'az login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Got access token"

# Build URL
URL="${API_BASE_URL}${ENDPOINT}"

# Make request
echo -e "${YELLOW}📡 ${METHOD} ${URL}${NC}"

if [ -n "$DATA" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" -X "$METHOD" "$URL" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$DATA")
else
    RESPONSE=$(curl -s -w "\n%{http_code}" -X "$METHOD" "$URL" \
        -H "Authorization: Bearer $TOKEN")
fi

# Parse response
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

# Display result
if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo -e "${GREEN}✓ HTTP $HTTP_CODE${NC}"
else
    echo -e "${RED}✗ HTTP $HTTP_CODE${NC}"
fi

# Pretty print JSON if jq available
if command -v jq &> /dev/null; then
    echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
else
    echo "$BODY"
fi
