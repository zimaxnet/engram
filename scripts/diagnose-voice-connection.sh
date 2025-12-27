#!/bin/bash
# Diagnose voice connection issues on Azure deployment

set -e

echo "=========================================="
echo "Voice Connection Diagnostic"
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

if [ -n "$SWA_URL" ] && [ "$SWA_URL" != "null" ]; then
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

echo "CORS_ORIGINS value: $CORS_VALUE"
echo ""

# Check if SWA URL is in CORS
if echo "$CORS_VALUE" | grep -q "engram.work" || echo "$CORS_VALUE" | grep -q "\*"; then
  echo "✓ SWA domain appears to be in CORS configuration"
else
  echo "⚠️  SWA domain may not be in CORS configuration"
fi
echo ""

# Test CORS preflight
echo "=========================================="
echo "2. Testing CORS Preflight"
echo "=========================================="
echo ""

CORS_TEST=$(curl -s -X OPTIONS "${BACKEND_URL}/api/v1/voice/realtime/token" \
  -H "Origin: ${SWA_URL}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -w "\nHTTP_CODE:%{http_code}" || echo "HTTP_CODE:000")

HTTP_CODE=$(echo "$CORS_TEST" | grep "HTTP_CODE:" | cut -d: -f2)
CORS_HEADERS=$(echo "$CORS_TEST" | sed '/HTTP_CODE:/d' | grep -i "access-control" || echo "No CORS headers")

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "204" ]; then
  echo "✓ CORS preflight successful (HTTP $HTTP_CODE)"
  echo "CORS headers:"
  echo "$CORS_HEADERS" | head -5
else
  echo "❌ CORS preflight failed (HTTP $HTTP_CODE)"
fi
echo ""

# Test actual endpoint
echo "=========================================="
echo "3. Testing Voice Token Endpoint"
echo "=========================================="
echo ""

TOKEN_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/v1/voice/realtime/token" \
  -H "Content-Type: application/json" \
  -H "Origin: ${SWA_URL}" \
  -d '{"agent_id":"elena","session_id":"test"}' \
  -w "\nHTTP_CODE:%{http_code}" || echo "HTTP_CODE:000")

HTTP_CODE=$(echo "$TOKEN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$TOKEN_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" == "200" ]; then
  echo "✓ Voice token endpoint accessible"
  echo "Response preview:"
  echo "$RESPONSE_BODY" | head -3
elif [ "$HTTP_CODE" == "401" ]; then
  echo "⚠️  Authentication required (HTTP 401)"
  echo "Check AUTH_REQUIRED setting"
elif [ "$HTTP_CODE" == "503" ]; then
  echo "⚠️  VoiceLive not configured (HTTP 503)"
  echo "Check AZURE_VOICELIVE_ENDPOINT and AZURE_VOICELIVE_KEY"
else
  echo "❌ Endpoint failed (HTTP $HTTP_CODE)"
  echo "Response: $RESPONSE_BODY"
fi
echo ""

# Check backend logs
echo "=========================================="
echo "4. Recent Backend Logs (last 10 lines)"
echo "=========================================="
echo ""

az containerapp logs show \
  --name "${ENVIRONMENT}-env-api" \
  --resource-group "$RESOURCE_GROUP" \
  --tail 10 \
  --type console 2>/dev/null | tail -10 || echo "Could not retrieve logs"
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "If CORS is the issue, update CORS_ORIGINS to include:"
echo "  - ${SWA_URL}"
echo "  - https://*.azurestaticapps.net (for default SWA hostnames)"
echo ""
echo "Update command:"
echo "  az containerapp update \\"
echo "    --name ${ENVIRONMENT}-env-api \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --set-env-vars 'CORS_ORIGINS=[\"${SWA_URL}\",\"https://*.azurestaticapps.net\",\"http://localhost:5173\"]'"
echo ""


