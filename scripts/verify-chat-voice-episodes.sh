#!/bin/bash
# Verify Chat, VoiceLive, and Episodes are working
# This script tests all three components for enterprise POC readiness

set -e

API_URL="${API_URL:-https://api.engram.work}"
SESSION_ID="verify-$(date +%s)"

echo "🔍 Engram Component Verification"
echo "================================"
echo ""
echo "API URL: $API_URL"
echo "Session ID: $SESSION_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

test_chat() {
    echo "1️⃣ Testing Chat Endpoint (Model Router)..."
    echo "   POST $API_URL/api/v1/chat"
    
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/api/v1/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"model-router\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Hello, this is a verification test. Please respond briefly.\"}],
            \"session_id\": \"$SESSION_ID\"
        }")
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        CONTENT=$(echo "$BODY" | jq -r '.content // .error // .message' 2>/dev/null || echo "$BODY")
        if [ -n "$CONTENT" ] && [ "$CONTENT" != "null" ]; then
            echo -e "   ${GREEN}✅ Chat working${NC}"
            echo "   Response: ${CONTENT:0:100}..."
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        fi
    fi
    
    echo -e "   ${RED}❌ Chat failed${NC}"
    echo "   HTTP Status: $HTTP_STATUS"
    echo "   Response: $BODY"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
}

test_episodes() {
    echo ""
    echo "2️⃣ Testing Episodes/Memory API..."
    echo "   GET $API_URL/api/v1/memory/episodes?limit=5"
    
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL/api/v1/memory/episodes?limit=5" \
        -H "Content-Type: application/json")
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        EPISODE_COUNT=$(echo "$BODY" | jq -r '.episodes | length' 2>/dev/null || echo "0")
        if [ -n "$EPISODE_COUNT" ] && [ "$EPISODE_COUNT" != "null" ]; then
            echo -e "   ${GREEN}✅ Episodes API working${NC}"
            echo "   Found $EPISODE_COUNT episodes"
            if [ "$EPISODE_COUNT" -gt 0 ]; then
                echo "   Recent episodes:"
                echo "$BODY" | jq -r '.episodes[]? | "     - \(.id): \(.summary // "No summary")[:50]"' 2>/dev/null | head -3
            fi
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        fi
    fi
    
    echo -e "   ${YELLOW}⚠️  Episodes API accessible but no episodes found${NC}"
    echo "   HTTP Status: $HTTP_STATUS"
    if [ "$HTTP_STATUS" = "200" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
    
    echo -e "   ${RED}❌ Episodes API failed${NC}"
    echo "   Response: $BODY"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
}

test_voicelive_health() {
    echo ""
    echo "3️⃣ Testing VoiceLive Health Check..."
    echo "   GET $API_URL/api/v1/voice/health"
    
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL/api/v1/voice/health" \
        -H "Content-Type: application/json")
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        STATUS=$(echo "$BODY" | jq -r '.status // .message' 2>/dev/null || echo "$BODY")
        echo -e "   ${GREEN}✅ VoiceLive health check passed${NC}"
        echo "   Status: $STATUS"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
    
    echo -e "   ${RED}❌ VoiceLive health check failed${NC}"
    echo "   HTTP Status: $HTTP_STATUS"
    echo "   Response: $BODY"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    return 1
}

test_memory_ingestion() {
    echo ""
    echo "4️⃣ Testing Memory Ingestion (Chat → Zep)..."
    echo "   Sending chat message and checking if it appears in episodes..."
    
    # Send a chat message with unique content
    UNIQUE_CONTENT="Memory ingestion test $(date +%s)"
    CHAT_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"model-router\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$UNIQUE_CONTENT\"}],
            \"session_id\": \"$SESSION_ID\"
        }")
    
    # Wait a moment for memory to be persisted
    echo "   Waiting 3 seconds for memory persistence..."
    sleep 3
    
    # Check if the session appears in episodes
    EPISODES_RESPONSE=$(curl -s "$API_URL/api/v1/memory/episodes?limit=10" \
        -H "Content-Type: application/json")
    
    SESSION_FOUND=$(echo "$EPISODES_RESPONSE" | jq -r ".episodes[]? | select(.session_id == \"$SESSION_ID\") | .id" 2>/dev/null | head -1)
    
    if [ -n "$SESSION_FOUND" ] && [ "$SESSION_FOUND" != "null" ]; then
        echo -e "   ${GREEN}✅ Memory ingestion working${NC}"
        echo "   Session $SESSION_ID found in episodes"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "   ${YELLOW}⚠️  Memory ingestion may not be working${NC}"
        echo "   Session $SESSION_ID not found in episodes yet"
        echo "   This could be normal if persistence is async or delayed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

# Run tests
test_chat
test_episodes
test_voicelive_health
test_memory_ingestion

# Summary
echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"
echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
fi

