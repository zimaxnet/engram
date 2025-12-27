#!/bin/bash
# Test VoiceLive configuration that works with deployed SWA
# This tests the endpoints the frontend actually uses

set -e

echo "=========================================="
echo "Testing VoiceLive Configuration for SWA"
echo "=========================================="
echo ""

RESOURCE_GROUP="${RESOURCE_GROUP:-engram-rg}"
ENVIRONMENT="${ENVIRONMENT:-staging}"

# Get backend URL
BACKEND_URL=$(az containerapp show \
  --name "${ENVIRONMENT}-env-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || \
  az containerapp show \
  --name "engram-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
  echo "❌ Could not get backend URL"
  exit 1
fi

BACKEND_URL="https://${BACKEND_URL}"
echo "Backend URL: $BACKEND_URL"
echo ""

# Get SWA URL
SWA_URL=$(az staticwebapp show \
  --name "${ENVIRONMENT}-env-web" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.defaultHostname" -o tsv 2>/dev/null || echo "engram.work")

if [ -n "$SWA_URL" ] && [ "$SWA_URL" != "null" ] && [ "$SWA_URL" != "" ]; then
  SWA_URL="https://${SWA_URL}"
else
  SWA_URL="https://engram.work"
fi

echo "SWA URL: $SWA_URL"
echo ""

# Check CORS configuration
echo "=========================================="
echo "1. Checking CORS Configuration"
echo "=========================================="
echo ""

CORS_VALUE=$(az containerapp show \
  --name "${ENVIRONMENT}-env-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.template.containers[0].env[?name=='CORS_ORIGINS'].value" -o tsv 2>/dev/null || echo "not found")

echo "CORS_ORIGINS: $CORS_VALUE"
echo ""

# Check if SWA URL is in CORS
if echo "$CORS_VALUE" | grep -q "engram.work" || echo "$CORS_VALUE" | grep -q "\*"; then
  echo "✓ SWA domain is in CORS configuration"
else
  echo "⚠️  SWA domain may not be in CORS configuration"
  echo "   Consider adding $SWA_URL to CORS_ORIGINS"
fi
echo ""

# Test endpoints that frontend uses
echo "=========================================="
echo "2. Testing Frontend Endpoints"
echo "=========================================="
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL/health" 2>/dev/null || echo "FAILED")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Health endpoint working"
  echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE" | grep -v "HTTP_CODE"
else
  echo "❌ Health endpoint failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test 2: Voice Status (used by frontend to check configuration)
echo "Test 2: Voice Status Endpoint"
STATUS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL/api/v1/voice/status" 2>/dev/null || echo "FAILED")
HTTP_CODE=$(echo "$STATUS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Voice status endpoint working"
  echo "$STATUS_RESPONSE" | grep -v "HTTP_CODE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE" | grep -v "HTTP_CODE"
else
  echo "❌ Voice status endpoint failed (HTTP $HTTP_CODE)"
  echo "$STATUS_RESPONSE" | grep -v "HTTP_CODE"
fi
echo ""

# Test 3: Voice Config (used by frontend to get agent config)
echo "Test 3: Voice Config Endpoint (Elena)"
CONFIG_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL/api/v1/voice/config/elena" 2>/dev/null || echo "FAILED")
HTTP_CODE=$(echo "$CONFIG_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Voice config endpoint working"
  echo "$CONFIG_RESPONSE" | grep -v "HTTP_CODE" | python3 -m json.tool 2>/dev/null || echo "$CONFIG_RESPONSE" | grep -v "HTTP_CODE"
else
  echo "❌ Voice config endpoint failed (HTTP $HTTP_CODE)"
  echo "$CONFIG_RESPONSE" | grep -v "HTTP_CODE"
fi
echo ""

# Test 4: Token Endpoint (known limitation with unified endpoints)
echo "Test 4: Voice Token Endpoint (Expected: 404 with unified endpoint)"
TOKEN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BACKEND_URL/api/v1/voice/realtime/token" \
  -H "Content-Type: application/json" \
  -H "Origin: $SWA_URL" \
  -d '{"agent_id":"elena","session_id":"test"}' 2>/dev/null || echo "FAILED")
HTTP_CODE=$(echo "$TOKEN_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ Token endpoint working (unexpected - may be using direct endpoint)"
  echo "$TOKEN_RESPONSE" | grep -v "HTTP_CODE" | python3 -m json.tool 2>/dev/null || echo "$TOKEN_RESPONSE" | grep -v "HTTP_CODE"
elif [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "502" ]; then
  echo "⚠️  Token endpoint returns $HTTP_CODE (expected with unified endpoint)"
  echo "   This is a known limitation - unified endpoints don't support REST token endpoint"
  echo "   Frontend should use WebSocket proxy endpoint instead: /api/v1/voice/voicelive/{session_id}"
  ERROR_MSG=$(echo "$TOKEN_RESPONSE" | grep -v "HTTP_CODE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null || echo "Unknown error")
  echo "   Error: $ERROR_MSG"
else
  echo "❌ Token endpoint failed (HTTP $HTTP_CODE)"
  echo "$TOKEN_RESPONSE" | grep -v "HTTP_CODE"
fi
echo ""

# Test 5: CORS preflight (check if frontend can make requests)
echo "Test 5: CORS Preflight Check"
CORS_RESPONSE=$(curl -s -X OPTIONS "$BACKEND_URL/api/v1/voice/status" \
  -H "Origin: $SWA_URL" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -w "\nHTTP_CODE:%{http_code}" 2>/dev/null || echo "FAILED")
HTTP_CODE=$(echo "$CORS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
CORS_HEADER=$(echo "$CORS_RESPONSE" | grep -i "access-control-allow-origin" || echo "")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
  if [ -n "$CORS_HEADER" ]; then
    echo "✓ CORS preflight successful"
    echo "  $CORS_HEADER"
  else
    echo "⚠️  CORS preflight responded but no Access-Control-Allow-Origin header"
  fi
else
  echo "❌ CORS preflight failed (HTTP $HTTP_CODE)"
fi
echo ""

# Summary
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo "SWA URL: $SWA_URL"
echo "CORS Origins: $CORS_VALUE"
echo ""

# Check VoiceLive configuration
VOICELIVE_ENDPOINT=$(az containerapp show \
  --name "${ENVIRONMENT}-env-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.template.containers[0].env[?name=='AZURE_VOICELIVE_ENDPOINT'].value" -o tsv 2>/dev/null || echo "not found")

VOICELIVE_MODEL=$(az containerapp show \
  --name "${ENVIRONMENT}-env-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.template.containers[0].env[?name=='AZURE_VOICELIVE_MODEL'].value" -o tsv 2>/dev/null || echo "not found")

echo "VoiceLive Configuration:"
echo "  Endpoint: $VOICELIVE_ENDPOINT"
echo "  Model: $VOICELIVE_MODEL"
echo ""

# Recommendations
echo "=========================================="
echo "Recommendations"
echo "=========================================="
echo ""

if echo "$VOICELIVE_ENDPOINT" | grep -q "services.ai.azure.com"; then
  echo "⚠️  Using unified endpoint (services.ai.azure.com)"
  echo "   - REST token endpoint (/realtime/token) is NOT supported"
  echo "   - Frontend should use WebSocket proxy: /api/v1/voice/voicelive/{session_id}"
  echo "   - OR switch to direct OpenAI endpoint (openai.azure.com) for token support"
elif echo "$VOICELIVE_ENDPOINT" | grep -q "openai.azure.com"; then
  echo "✓ Using direct OpenAI endpoint (openai.azure.com)"
  echo "   - REST token endpoint should work"
  echo "   - Frontend can use either token endpoint or WebSocket proxy"
else
  echo "⚠️  Unknown endpoint type"
fi
echo ""

if ! echo "$CORS_VALUE" | grep -q "engram.work" && ! echo "$CORS_VALUE" | grep -q "\*"; then
  echo "⚠️  CORS configuration may need update"
  echo "   Add $SWA_URL to CORS_ORIGINS environment variable"
fi
echo ""

echo "✅ Test complete!"
echo ""

