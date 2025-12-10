#!/bin/bash

# Engram Platform - Complete Function Testing Script
# This script tests all major functions of the Engram platform

set -e

FRONTEND_URL="https://engram.work"
BACKEND_URL="https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io"
API_BASE="${BACKEND_URL}/api/v1"

echo "=========================================="
echo "Engram Platform - Function Testing"
echo "=========================================="
echo ""
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local method=$2
    local url=$3
    local data=$4
    local max_time=${5:-60}  # Default 60 seconds, longer for cold starts
    local retries=${6:-3}    # Default 3 retries
    
    echo -n "Testing $name... "
    
    local attempt=1
    local success=0
    
    while [ $attempt -le $retries ]; do
        if [ "$method" = "GET" ]; then
            response=$(curl -s --max-time $max_time -w "\n%{http_code}" "$url" 2>&1)
        else
            response=$(curl -s --max-time $max_time -X "$method" -H "Content-Type: application/json" -d "$data" -w "\n%{http_code}" "$url" 2>&1)
        fi
        
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo -e "${GREEN}✓${NC} (HTTP $http_code)"
            if [ ! -z "$body" ] && [ "$body" != "null" ]; then
                echo "$body" | jq '.' 2>/dev/null || echo "  Response: $body"
            fi
            success=1
            break
        elif [ "$http_code" = "000" ] || [ -z "$http_code" ]; then
            # Timeout or connection error - likely cold start
            if [ $attempt -lt $retries ]; then
                echo -n "(attempt $attempt/$retries, waiting for cold start...) "
                sleep 10
                attempt=$((attempt + 1))
                continue
            else
                echo -e "${YELLOW}⚠${NC} (Timeout - backend may be cold starting)"
                echo "  This is normal for the first request. Try again in 30-60 seconds."
                return 1
            fi
        else
            echo -e "${RED}✗${NC} (HTTP $http_code)"
            echo "  Response: $body"
            return 1
        fi
    done
    
    if [ $success -eq 1 ]; then
        return 0
    else
        return 1
    fi
}

# =============================================================================
# 1. Health & Readiness
# =============================================================================
echo "=== 1. Health & Readiness ==="
echo "Note: Backend may be scaled to zero - first request may take 30-60 seconds"
echo ""

test_endpoint "Health Check" "GET" "${API_BASE}/health" "" 90 5
echo ""

test_endpoint "Readiness Check" "GET" "${API_BASE}/ready" "" 90 5
echo ""

# =============================================================================
# 2. Agents API
# =============================================================================
echo "=== 2. Agents API ==="
echo ""

test_endpoint "List All Agents" "GET" "${API_BASE}/agents"
echo ""

test_endpoint "Get Elena Details" "GET" "${API_BASE}/agents/elena"
echo ""

test_endpoint "Get Marcus Details" "GET" "${API_BASE}/agents/marcus"
echo ""

# =============================================================================
# 3. Chat API
# =============================================================================
echo "=== 3. Chat API ==="
echo ""

SESSION_ID="test-session-$(date +%s)"

test_endpoint "Send Chat Message (Elena)" "POST" "${API_BASE}/chat" \
    "{\"content\": \"Hello, can you introduce yourself?\", \"agent_id\": \"elena\", \"session_id\": \"$SESSION_ID\"}"
echo ""

test_endpoint "Send Chat Message (Marcus)" "POST" "${API_BASE}/chat" \
    "{\"content\": \"What is your role?\", \"agent_id\": \"marcus\", \"session_id\": \"$SESSION_ID\"}"
echo ""

echo "Note: WebSocket testing requires interactive testing"
echo "  WebSocket URL: wss://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io/api/v1/chat/ws/$SESSION_ID"
echo ""

# =============================================================================
# 4. Voice API
# =============================================================================
echo "=== 4. Voice API ==="
echo ""

echo "Note: Voice endpoints require audio data"
echo "  Transcribe: POST ${API_BASE}/voice/transcribe"
echo "  Synthesize: POST ${API_BASE}/voice/synthesize"
echo "  Voice WebSocket: wss://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io/api/v1/voice/ws/$SESSION_ID"
echo ""

# =============================================================================
# 5. Memory API
# =============================================================================
echo "=== 5. Memory API ==="
echo ""

test_endpoint "Search Memory" "GET" "${API_BASE}/memory/search?query=test"
echo ""

test_endpoint "List Episodes" "GET" "${API_BASE}/memory/episodes?limit=10"
echo ""

# =============================================================================
# 6. Workflows API
# =============================================================================
echo "=== 6. Workflows API ==="
echo ""

test_endpoint "List Workflows" "GET" "${API_BASE}/workflows"
echo ""

# =============================================================================
# 7. Frontend
# =============================================================================
echo "=== 7. Frontend ==="
echo ""

echo -n "Testing Frontend Accessibility... "
if curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200"; then
    echo -e "${GREEN}✓${NC} (HTTP 200)"
    echo "  Frontend is accessible at: $FRONTEND_URL"
else
    echo -e "${RED}✗${NC}"
fi
echo ""

# =============================================================================
# Summary
# =============================================================================
echo "=========================================="
echo "Testing Complete"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Open $FRONTEND_URL in your browser"
echo "2. Test interactive features:"
echo "   - Chat with Elena and Marcus"
echo "   - Voice controls"
echo "   - Agent switching"
echo "   - Visual panel metrics"
echo ""
echo "3. Check browser console (F12) for any errors"
echo "4. Test WebSocket connections from the frontend"
echo ""

