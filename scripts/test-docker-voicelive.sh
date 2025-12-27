#!/bin/bash
# Test VoiceLive configuration in Docker container

set -e

echo "=========================================="
echo "Testing VoiceLive in Docker Container"
echo "=========================================="
echo ""

# Get Azure configuration
AZURE_VOICELIVE_ENDPOINT="${AZURE_VOICELIVE_ENDPOINT:-https://zimax.services.ai.azure.com}"
AZURE_VOICELIVE_KEY="${AZURE_VOICELIVE_KEY:-}"
AZURE_VOICELIVE_MODEL="${AZURE_VOICELIVE_MODEL:-gpt-realtime}"
AZURE_VOICELIVE_PROJECT_NAME="${AZURE_VOICELIVE_PROJECT_NAME:-zimax}"
AZURE_VOICELIVE_API_VERSION="${AZURE_VOICELIVE_API_VERSION:-2024-10-01-preview}"

if [ -z "$AZURE_VOICELIVE_KEY" ]; then
  echo "⚠️  AZURE_VOICELIVE_KEY not set. Getting from Key Vault..."
  AZURE_VOICELIVE_KEY=$(az keyvault secret show \
    --vault-name stagingenvkvysoxm5 \
    --name voicelive-api-key \
    --query "value" -o tsv 2>/dev/null || echo "")
  
  if [ -z "$AZURE_VOICELIVE_KEY" ]; then
    echo "❌ Could not get AZURE_VOICELIVE_KEY"
    echo "   Set it manually: export AZURE_VOICELIVE_KEY='your-key'"
    exit 1
  fi
fi

echo "Configuration:"
echo "  Endpoint: $AZURE_VOICELIVE_ENDPOINT"
echo "  Model: $AZURE_VOICELIVE_MODEL"
echo "  Project: $AZURE_VOICELIVE_PROJECT_NAME"
echo "  API Version: $AZURE_VOICELIVE_API_VERSION"
echo ""

# Build image if not exists
if ! docker image inspect engram-backend:local >/dev/null 2>&1; then
  echo "Building Docker image..."
  docker build -t engram-backend:local -f backend/Dockerfile backend/
  echo ""
fi

# Stop and remove existing container if running
echo "Cleaning up existing container..."
docker stop engram-backend-test 2>/dev/null || true
docker rm engram-backend-test 2>/dev/null || true
echo ""

# Run container with VoiceLive configuration
echo "Starting container with VoiceLive configuration..."
docker run -d \
  --name engram-backend-test \
  -p 8082:8080 \
  -e ENVIRONMENT=development \
  -e DEBUG=true \
  -e AUTH_REQUIRED=false \
  -e AZURE_VOICELIVE_ENDPOINT="$AZURE_VOICELIVE_ENDPOINT" \
  -e AZURE_VOICELIVE_KEY="$AZURE_VOICELIVE_KEY" \
  -e AZURE_VOICELIVE_MODEL="$AZURE_VOICELIVE_MODEL" \
  -e AZURE_VOICELIVE_PROJECT_NAME="$AZURE_VOICELIVE_PROJECT_NAME" \
  -e AZURE_VOICELIVE_API_VERSION="$AZURE_VOICELIVE_API_VERSION" \
  -e CORS_ORIGINS='["http://localhost:5173", "http://localhost:3000", "*"]' \
  engram-backend:local

echo "Waiting for container to start..."
sleep 5

# Check if container is running
if ! docker ps | grep -q engram-backend-test; then
  echo "❌ Container failed to start"
  echo "Logs:"
  docker logs engram-backend-test
  exit 1
fi

echo "✓ Container is running"
echo ""

# Wait for health check
echo "Waiting for API to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8082/health >/dev/null 2>&1; then
    echo "✓ API is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "❌ API did not become ready"
    echo "Logs:"
    docker logs engram-backend-test | tail -20
    exit 1
  fi
  sleep 1
done
echo ""

# Test VoiceLive endpoints
echo "=========================================="
echo "Testing VoiceLive Endpoints"
echo "=========================================="
echo ""

# Test 1: Voice Status
echo "Test 1: Voice Status Endpoint"
STATUS_RESPONSE=$(curl -s http://localhost:8082/api/v1/voice/status)
if echo "$STATUS_RESPONSE" | grep -q "voicelive_configured"; then
  echo "✓ Voice status endpoint working"
  echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
else
  echo "❌ Voice status endpoint failed"
  echo "$STATUS_RESPONSE"
fi
echo ""

# Test 2: Voice Config (Elena)
echo "Test 2: Voice Config (Elena)"
CONFIG_RESPONSE=$(curl -s http://localhost:8082/api/v1/voice/config/elena)
if echo "$CONFIG_RESPONSE" | grep -q "voice_name"; then
  echo "✓ Voice config endpoint working"
  echo "$CONFIG_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CONFIG_RESPONSE"
else
  echo "❌ Voice config endpoint failed"
  echo "$CONFIG_RESPONSE"
fi
echo ""

# Test 3: Token Endpoint
echo "Test 3: Voice Token Endpoint"
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8082/api/v1/voice/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"elena","session_id":"test"}')
if echo "$TOKEN_RESPONSE" | grep -q "token\|error"; then
  if echo "$TOKEN_RESPONSE" | grep -q '"token"'; then
    echo "✓ Token endpoint working"
    echo "$TOKEN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TOKEN_RESPONSE"
  else
    echo "⚠️  Token endpoint responded but may have errors:"
    echo "$TOKEN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TOKEN_RESPONSE"
  fi
else
  echo "❌ Token endpoint failed"
  echo "$TOKEN_RESPONSE"
fi
echo ""

# Show container logs
echo "=========================================="
echo "Container Logs (last 20 lines)"
echo "=========================================="
docker logs engram-backend-test 2>&1 | tail -20
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Container: engram-backend-test"
echo "API URL: http://localhost:8082"
echo ""
echo "To view logs: docker logs -f engram-backend-test"
echo "To stop: docker stop engram-backend-test"
echo "To remove: docker rm engram-backend-test"
echo ""

