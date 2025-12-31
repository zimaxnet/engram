#!/bin/bash
# scripts/verify_fixes.sh

API_URL="https://api.engram.work"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔍 Verifying Specific Bug Fixes"
echo "=============================="

# 1. Test "model-router" Agent ID Fix
echo ""
echo "1️⃣ Testing Chat with 'model-router' Agent ID..."
echo "   Previous behavior: 500 Error / Fallback message"
echo "   Expected behavior: 200 OK (Auto-routed)"

CHAT_PAYLOAD='{
  "content": "Hello, are you working?",
  "agent_id": "model-router"
}'

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "$CHAT_PAYLOAD")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    # Check if we got a real response vs the fallback error message
    if [[ "$BODY" == *"I apologize"* && "$BODY" == *"logs"* ]]; then
         echo -e "   ${RED}❌ Fix Failed: Still getting fallback error message${NC}"
         echo "   Response: $BODY"
    else
         echo -e "   ${GREEN}✅ Fix Verified: 'model-router' request succeeded${NC}"
         echo "   Response excerpt: ${BODY:0:100}..."
    fi
else
    echo -e "   ${RED}❌ Fix Failed: HTTP $HTTP_STATUS${NC}"
    echo "   Response: $BODY"
fi

echo ""
echo "2️⃣ Google Auth Verification"
echo "   This requires manual verification in the browser."
echo "   Navigate to https://engram.work and click 'Continue with Google'."
echo "   If you see the Google account picker instead of Error 400, the fix worked."
