#!/bin/bash
# Test video token generation endpoint in container

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8082}"
AGENT_ID="${AGENT_ID:-elena}"

echo "============================================================"
echo "Testing Video Token Generation (Container)"
echo "============================================================"
echo ""
echo "Backend URL: $BACKEND_URL"
echo "Agent ID: $AGENT_ID"
echo ""

# Test video token generation
echo "Test: Video token generation with modalities=['video', 'text']"
echo "------------------------------------------------------------"

curl -X POST "${BACKEND_URL}/api/v1/voice/realtime/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_id\": \"${AGENT_ID}\",
    \"modalities\": [\"video\", \"text\"]
  }" \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -s | jq '.' || echo "Response (raw):"
  
echo ""
echo "============================================================"

