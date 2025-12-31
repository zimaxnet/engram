#!/bin/bash
#
# Test Authentication Fix
#
# This script tests the authentication flow after the fix to verify:
# 1. Google login works
# 2. Token validation works
# 3. All API endpoints (chat, voice, episodes, stories) accept authenticated requests
#

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get API URL from environment or use default
API_URL="${VITE_API_URL:-https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Engram Authentication Fix Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "API URL: $API_URL"
echo ""

# Check if AUTH_TOKEN is provided
if [ -z "$AUTH_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  AUTH_TOKEN not provided${NC}"
    echo ""
    echo "To test with a real token:"
    echo "  1. Login via Google in the frontend"
    echo "  2. Get token from browser DevTools:"
    echo "     - Open DevTools (F12)"
    echo "     - Go to Application > Local Storage"
    echo "     - Look for MSAL tokens"
    echo "     - Or check Network tab for Authorization header"
    echo ""
    echo "  3. Run: AUTH_TOKEN='your-token' $0"
    echo ""
    echo -e "${YELLOW}Testing without token (will test health endpoint only)...${NC}"
    echo ""
    
    # Test health endpoint (should work without auth)
    echo -e "${BLUE}1️⃣  Testing Health Endpoint (no auth required)...${NC}"
    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health" || echo -e "\n000")
    HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tail -n1)
    HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')
    
    if [ "$HEALTH_STATUS" = "200" ]; then
        echo -e "   ${GREEN}✅ Health check passed${NC}"
        echo "   Response: $(echo "$HEALTH_BODY" | jq -r '.status // "OK"' 2>/dev/null || echo "OK")"
    else
        echo -e "   ${RED}❌ Health check failed (HTTP $HEALTH_STATUS)${NC}"
    fi
    echo ""
    
    echo -e "${YELLOW}To test authenticated endpoints, provide AUTH_TOKEN${NC}"
    exit 0
fi

echo -e "${GREEN}✅ AUTH_TOKEN provided${NC}"
echo ""

# Test 1: Health endpoint (should work without auth)
echo -e "${BLUE}1️⃣  Testing Health Endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health" || echo -e "\n000")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ Health check passed${NC}"
else
    echo -e "   ${RED}❌ Health check failed (HTTP $HEALTH_STATUS)${NC}"
fi
echo ""

# Test 2: Chat endpoint
echo -e "${BLUE}2️⃣  Testing Chat Endpoint (/api/v1/chat)...${NC}"
CHAT_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content": "Hello, this is a test message", "agent_id": "elena"}' \
    "$API_URL/api/v1/chat" || echo -e "\n000")
CHAT_STATUS=$(echo "$CHAT_RESPONSE" | tail -n1)
CHAT_BODY=$(echo "$CHAT_RESPONSE" | sed '$d')

if [ "$CHAT_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ Chat endpoint works${NC}"
    MESSAGE_ID=$(echo "$CHAT_BODY" | jq -r '.message_id // "N/A"' 2>/dev/null || echo "N/A")
    AGENT_NAME=$(echo "$CHAT_BODY" | jq -r '.agent_name // "N/A"' 2>/dev/null || echo "N/A")
    echo "   Message ID: $MESSAGE_ID"
    echo "   Agent: $AGENT_NAME"
elif [ "$CHAT_STATUS" = "401" ]; then
    echo -e "   ${RED}❌ Chat endpoint returned 401 Unauthorized${NC}"
    echo "   Error: $(echo "$CHAT_BODY" | jq -r '.detail // .message // "Unauthorized"' 2>/dev/null || echo "Unauthorized")"
else
    echo -e "   ${RED}❌ Chat endpoint failed (HTTP $CHAT_STATUS)${NC}"
    echo "   Response: $(echo "$CHAT_BODY" | head -c 200)"
fi
echo ""

# Test 3: Episodes/Memory endpoint
echo -e "${BLUE}3️⃣  Testing Episodes Endpoint (/api/v1/memory/episodes)...${NC}"
EPISODES_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    "$API_URL/api/v1/memory/episodes?limit=5" || echo -e "\n000")
EPISODES_STATUS=$(echo "$EPISODES_RESPONSE" | tail -n1)
EPISODES_BODY=$(echo "$EPISODES_RESPONSE" | sed '$d')

if [ "$EPISODES_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ Episodes endpoint works${NC}"
    EPISODE_COUNT=$(echo "$EPISODES_BODY" | jq -r '.episodes | length // 0' 2>/dev/null || echo "0")
    TOTAL_COUNT=$(echo "$EPISODES_BODY" | jq -r '.total_count // 0' 2>/dev/null || echo "0")
    echo "   Episodes returned: $EPISODE_COUNT"
    echo "   Total episodes: $TOTAL_COUNT"
elif [ "$EPISODES_STATUS" = "401" ]; then
    echo -e "   ${RED}❌ Episodes endpoint returned 401 Unauthorized${NC}"
    echo "   Error: $(echo "$EPISODES_BODY" | jq -r '.detail // .message // "Unauthorized"' 2>/dev/null || echo "Unauthorized")"
else
    echo -e "   ${RED}❌ Episodes endpoint failed (HTTP $EPISODES_STATUS)${NC}"
    echo "   Response: $(echo "$EPISODES_BODY" | head -c 200)"
fi
echo ""

# Test 4: Stories endpoint
echo -e "${BLUE}4️⃣  Testing Stories Endpoint (/api/v1/story/)...${NC}"
STORIES_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    "$API_URL/api/v1/story/" || echo -e "\n000")
STORIES_STATUS=$(echo "$STORIES_RESPONSE" | tail -n1)
STORIES_BODY=$(echo "$STORIES_RESPONSE" | sed '$d')

if [ "$STORIES_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ Stories endpoint works${NC}"
    STORY_COUNT=$(echo "$STORIES_BODY" | jq -r '. | length // 0' 2>/dev/null || echo "0")
    echo "   Stories returned: $STORY_COUNT"
elif [ "$STORIES_STATUS" = "401" ]; then
    echo -e "   ${RED}❌ Stories endpoint returned 401 Unauthorized${NC}"
    echo "   Error: $(echo "$STORIES_BODY" | jq -r '.detail // .message // "Unauthorized"' 2>/dev/null || echo "Unauthorized")"
else
    echo -e "   ${RED}❌ Stories endpoint failed (HTTP $STORIES_STATUS)${NC}"
    echo "   Response: $(echo "$STORIES_BODY" | head -c 200)"
fi
echo ""

# Test 5: Voice token endpoint
echo -e "${BLUE}5️⃣  Testing Voice Token Endpoint (/api/v1/voice/realtime/token)...${NC}"
VOICE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"agent_id": "elena", "session_id": "test-session"}' \
    "$API_URL/api/v1/voice/realtime/token" || echo -e "\n000")
VOICE_STATUS=$(echo "$VOICE_RESPONSE" | tail -n1)
VOICE_BODY=$(echo "$VOICE_RESPONSE" | sed '$d')

if [ "$VOICE_STATUS" = "200" ]; then
    echo -e "   ${GREEN}✅ Voice token endpoint works${NC}"
    TOKEN_PRESENT=$(echo "$VOICE_BODY" | jq -r '.token // empty' 2>/dev/null || echo "")
    if [ -n "$TOKEN_PRESENT" ]; then
        echo "   Token received: ✅"
    else
        echo "   Token received: ❌"
    fi
elif [ "$VOICE_STATUS" = "401" ]; then
    echo -e "   ${RED}❌ Voice token endpoint returned 401 Unauthorized${NC}"
    echo "   Error: $(echo "$VOICE_BODY" | jq -r '.detail // .message // "Unauthorized"' 2>/dev/null || echo "Unauthorized")"
else
    echo -e "   ${RED}❌ Voice token endpoint failed (HTTP $VOICE_STATUS)${NC}"
    echo "   Response: $(echo "$VOICE_BODY" | head -c 200)"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Count successes and failures
SUCCESS_COUNT=0
FAIL_COUNT=0

[ "$HEALTH_STATUS" = "200" ] && SUCCESS_COUNT=$((SUCCESS_COUNT + 1)) || FAIL_COUNT=$((FAIL_COUNT + 1))
[ "$CHAT_STATUS" = "200" ] && SUCCESS_COUNT=$((SUCCESS_COUNT + 1)) || FAIL_COUNT=$((FAIL_COUNT + 1))
[ "$EPISODES_STATUS" = "200" ] && SUCCESS_COUNT=$((SUCCESS_COUNT + 1)) || FAIL_COUNT=$((FAIL_COUNT + 1))
[ "$STORIES_STATUS" = "200" ] && SUCCESS_COUNT=$((SUCCESS_COUNT + 1)) || FAIL_COUNT=$((FAIL_COUNT + 1))
[ "$VOICE_STATUS" = "200" ] && SUCCESS_COUNT=$((SUCCESS_COUNT + 1)) || FAIL_COUNT=$((FAIL_COUNT + 1))

echo "Tests passed: $SUCCESS_COUNT"
echo "Tests failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Authentication fix is working.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above for details.${NC}"
    echo ""
    echo "If you see 401 errors, the token may be:"
    echo "  - Expired (get a fresh token)"
    echo "  - Invalid format"
    echo "  - Missing required scopes"
    echo ""
    echo "Use the diagnostic script to inspect the token:"
    echo "  AUTH_TOKEN='your-token' python3 scripts/diagnose-auth-token.py"
    exit 1
fi

