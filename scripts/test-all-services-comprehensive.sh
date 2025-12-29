#!/bin/bash
# Comprehensive Test for All Services (Enterprise POC)
# Tests: Chat, Voice, Episodes, Stories, Artifacts

set -e

API_URL="${API_URL:-https://api.engram.work}"
FAILED=0
PASSED=0

echo "🧪 Comprehensive Service Test (Enterprise POC)"
echo "=============================================="
echo "API URL: $API_URL"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo ""

# Test 1: Health Check
echo "1. Health Check:"
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL/health" 2>&1)
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 || echo "000")
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_STATUS/d' | head -1)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "   ✅ Health: HTTP $HEALTH_STATUS"
    ((PASSED++))
else
    echo "   ❌ Health: HTTP $HEALTH_STATUS"
    echo "   Response: ${HEALTH_BODY:0:200}"
    ((FAILED++))
fi

# Test 2: Chat Endpoint
echo ""
echo "2. Chat Endpoint:"
CHAT_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST "$API_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello, this is a test","agent_id":"elena","session_id":"test-session-'$(date +%s)'"}' 2>&1)

CHAT_STATUS=$(echo "$CHAT_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 || echo "000")
CHAT_BODY=$(echo "$CHAT_RESPONSE" | sed '/HTTP_STATUS/d' | head -1)

if [ "$CHAT_STATUS" = "200" ]; then
    echo "   ✅ Chat: HTTP $CHAT_STATUS"
    echo "   Response preview: ${CHAT_BODY:0:100}..."
    ((PASSED++))
else
    echo "   ❌ Chat: HTTP $CHAT_STATUS"
    echo "   Response: ${CHAT_BODY:0:200}"
    ((FAILED++))
fi

# Test 3: Episodes Endpoint
echo ""
echo "3. Episodes Endpoint:"
EPISODES_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "$API_URL/api/v1/memory/episodes?limit=5" \
  -H "Content-Type: application/json" 2>&1)

EPISODES_STATUS=$(echo "$EPISODES_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 || echo "000")
EPISODES_BODY=$(echo "$EPISODES_RESPONSE" | sed '/HTTP_STATUS/d' | head -1)

if [ "$EPISODES_STATUS" = "200" ]; then
    EPISODE_COUNT=$(echo "$EPISODES_BODY" | jq -r '.episodes | length' 2>/dev/null || echo "0")
    echo "   ✅ Episodes: HTTP $EPISODES_STATUS (found $EPISODE_COUNT episodes)"
    ((PASSED++))
else
    echo "   ❌ Episodes: HTTP $EPISODES_STATUS"
    echo "   Response: ${EPISODES_BODY:0:200}"
    ((FAILED++))
fi

# Test 4: Voice Status
echo ""
echo "4. Voice Status:"
VOICE_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "$API_URL/api/v1/voice/status" \
  -H "Content-Type: application/json" 2>&1)

VOICE_STATUS=$(echo "$VOICE_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 || echo "000")
VOICE_BODY=$(echo "$VOICE_RESPONSE" | sed '/HTTP_STATUS/d' | head -1)

if [ "$VOICE_STATUS" = "200" ]; then
    echo "   ✅ Voice Status: HTTP $VOICE_STATUS"
    echo "   Response: ${VOICE_BODY:0:100}..."
    ((PASSED++))
else
    echo "   ❌ Voice Status: HTTP $VOICE_STATUS"
    echo "   Response: ${VOICE_BODY:0:200}"
    ((FAILED++))
fi

# Test 5: Stories List
echo ""
echo "5. Stories List:"
STORIES_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "$API_URL/api/v1/story" \
  -H "Content-Type: application/json" 2>&1)

STORIES_STATUS=$(echo "$STORIES_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 || echo "000")
STORIES_BODY=$(echo "$STORIES_RESPONSE" | sed '/HTTP_STATUS/d' | head -1)

if [ "$STORIES_STATUS" = "200" ]; then
    STORY_COUNT=$(echo "$STORIES_BODY" | jq -r '. | length' 2>/dev/null || echo "0")
    echo "   ✅ Stories: HTTP $STORIES_STATUS (found $STORY_COUNT stories)"
    ((PASSED++))
else
    echo "   ❌ Stories: HTTP $STORIES_STATUS"
    echo "   Response: ${STORIES_BODY:0:200}"
    ((FAILED++))
fi

# Test 6: Latest Story
echo ""
echo "6. Latest Story:"
LATEST_STORY_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  "$API_URL/api/v1/story/latest" \
  -H "Content-Type: application/json" 2>&1)

LATEST_STATUS=$(echo "$LATEST_STORY_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2 || echo "000")
LATEST_BODY=$(echo "$LATEST_STORY_RESPONSE" | sed '/HTTP_STATUS/d' | head -1)

if [ "$LATEST_STATUS" = "200" ] || [ "$LATEST_STATUS" = "404" ]; then
    if [ "$LATEST_STATUS" = "404" ]; then
        echo "   ⚠️  Latest Story: HTTP $LATEST_STATUS (no stories yet - acceptable)"
    else
        echo "   ✅ Latest Story: HTTP $LATEST_STATUS"
    fi
    ((PASSED++))
else
    echo "   ❌ Latest Story: HTTP $LATEST_STATUS"
    echo "   Response: ${LATEST_BODY:0:200}"
    ((FAILED++))
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✅ All services operational!"
    exit 0
else
    echo "❌ Some services are failing - investigation needed"
    echo ""
    echo "Next steps:"
    echo "1. Check deployment status: gh run list --limit 1"
    echo "2. Check backend logs: az containerapp logs show --name staging-env-api --resource-group engram-rg --tail 100"
    echo "3. Verify AUTH_REQUIRED setting: az containerapp show --name staging-env-api --resource-group engram-rg --query 'properties.template.containers[0].env' | grep AUTH_REQUIRED"
    exit 1
fi

