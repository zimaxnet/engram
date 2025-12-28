#!/bin/bash
# Test All Endpoints (Chat, VoiceLive, Episodes)
# Quick test to verify all three services are working

set -e

API_URL="${API_URL:-https://api.engram.work}"

echo "🧪 Testing All Endpoints"
echo "========================"
echo "API URL: $API_URL"
echo ""

# Test Chat
echo "1. Testing Chat Endpoint:"
CHAT_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST "$API_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"model": "model-router", "messages": [{"role": "user", "content": "test"}], "session_id": "test-123"}')

CHAT_STATUS=$(echo "$CHAT_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
CHAT_BODY=$(echo "$CHAT_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$CHAT_STATUS" = "200" ]; then
    echo "   ✅ Chat: HTTP $CHAT_STATUS"
else
    echo "   ❌ Chat: HTTP $CHAT_STATUS"
    echo "   Response: ${CHAT_BODY:0:100}"
fi

# Test Episodes
echo ""
echo "2. Testing Episodes API:"
EPISODES_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "$API_URL/api/v1/memory/episodes?limit=5" \
  -H "Content-Type: application/json")

EPISODES_STATUS=$(echo "$EPISODES_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
EPISODES_BODY=$(echo "$EPISODES_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$EPISODES_STATUS" = "200" ]; then
    EPISODE_COUNT=$(echo "$EPISODES_BODY" | jq -r '.episodes | length' 2>/dev/null || echo "0")
    echo "   ✅ Episodes: HTTP $EPISODES_STATUS (found $EPISODE_COUNT episodes)"
else
    echo "   ❌ Episodes: HTTP $EPISODES_STATUS"
    echo "   Response: ${EPISODES_BODY:0:100}"
fi

# Test VoiceLive Health
echo ""
echo "3. Testing VoiceLive Health:"
VOICE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "$API_URL/api/v1/voice/health" \
  -H "Content-Type: application/json")

VOICE_STATUS=$(echo "$VOICE_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
VOICE_BODY=$(echo "$VOICE_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$VOICE_STATUS" = "200" ]; then
    echo "   ✅ VoiceLive: HTTP $VOICE_STATUS"
else
    echo "   ❌ VoiceLive: HTTP $VOICE_STATUS"
    echo "   Response: ${VOICE_BODY:0:100}"
fi

echo ""
echo "📊 Summary"
echo "=========="
if [ "$CHAT_STATUS" = "200" ] && [ "$EPISODES_STATUS" = "200" ] && [ "$VOICE_STATUS" = "200" ]; then
    echo "✅ All endpoints working!"
    exit 0
else
    echo "❌ Some endpoints failing"
    exit 1
fi

