#!/bin/bash
# Test Chat Functionality in Azure

set -e

echo "============================================================"
echo "Azure Chat Functionality Test"
echo "============================================================"
echo ""

# Get API FQDN
API_FQDN=$(az containerapp show \
  --name staging-env-api \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv 2>/dev/null)

if [ -z "$API_FQDN" ]; then
    echo "❌ Could not get API FQDN. Is the container app running?"
    exit 1
fi

API_URL="https://${API_FQDN}"

echo "🌐 API URL: $API_URL"
echo ""

# Test 1: Health Check
echo "📋 Test 1: Health Check"
echo "-----------------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/health" 2>&1)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check: SUCCESS (HTTP $HTTP_CODE)"
else
    echo "❌ Health check: FAILED (HTTP $HTTP_CODE)"
    echo "   Response: $BODY"
    exit 1
fi

echo ""

# Test 2: Chat Endpoint (requires auth, so we'll test the endpoint exists)
echo "📋 Test 2: Chat Endpoint Availability"
echo "-----------------------------------"
CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello", "agent_id": "elena"}' 2>&1)
HTTP_CODE=$(echo "$CHAT_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Chat endpoint: AVAILABLE (HTTP $HTTP_CODE)"
    if [ "$HTTP_CODE" = "401" ]; then
        echo "   Note: Authentication required (expected for production)"
    fi
else
    echo "❌ Chat endpoint: ERROR (HTTP $HTTP_CODE)"
    echo "   Response: $(echo "$CHAT_RESPONSE" | sed '$d')"
    exit 1
fi

echo ""

# Test 3: Check Logs for Model Router
echo "📋 Test 3: Checking Logs for Model Router"
echo "-----------------------------------"
echo "   Checking recent logs for Model Router usage..."
echo ""
echo "   Run this command to view logs:"
echo "   az containerapp logs show --name staging-env-api --resource-group engram-rg --follow"
echo ""
echo "   Look for: 'Using Model Router via APIM Gateway: model-router'"

echo ""
echo "============================================================"
echo "✅ Basic connectivity tests passed!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Test chat from the frontend UI"
echo "  2. Check logs for Model Router usage"
echo "  3. Verify no errors in Container Apps logs"

