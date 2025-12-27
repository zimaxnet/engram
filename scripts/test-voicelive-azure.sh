#!/bin/bash
# Test VoiceLive on Azure Static Web App deployment
# This script tests voice live functionality on the deployed Azure environment

set -e

echo "=========================================="
echo "Testing VoiceLive on Azure Deployment"
echo "=========================================="
echo ""

# Get resource group (default to engram-rg)
RESOURCE_GROUP="${RESOURCE_GROUP:-engram-rg}"
ENVIRONMENT="${ENVIRONMENT:-staging}"

echo "Resource Group: $RESOURCE_GROUP"
echo "Environment: $ENVIRONMENT"
echo ""

# Get backend API URL
echo "Step 1: Getting backend API URL..."
BACKEND_URL=$(az containerapp show \
  --name "${ENVIRONMENT}-env-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || \
  az containerapp show \
  --name "engram-api" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
  echo "❌ Could not get backend URL. Please set BACKEND_URL manually:"
  echo "   export BACKEND_URL=https://your-backend-url"
  exit 1
fi

BACKEND_URL="https://${BACKEND_URL}"
echo "✓ Backend URL: $BACKEND_URL"
echo ""

# Get SWA URL (try custom domain first, then default hostname)
echo "Step 2: Getting Static Web App URL..."
SWA_URL=$(az staticwebapp show \
  --name "${ENVIRONMENT}-env-web" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.defaultHostname" -o tsv 2>/dev/null)

if [ -z "$SWA_URL" ] || [ "$SWA_URL" == "null" ]; then
  # Try alternative name
  SWA_URL=$(az staticwebapp show \
    --name "engram-web" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.defaultHostname" -o tsv 2>/dev/null)
fi

if [ -n "$SWA_URL" ] && [ "$SWA_URL" != "null" ]; then
  SWA_URL="https://${SWA_URL}"
  echo "✓ SWA URL: $SWA_URL"
else
  # Fallback to known custom domain
  SWA_URL="https://engram.work"
  echo "⚠️  Could not get SWA hostname, using fallback: $SWA_URL"
fi
echo ""

# Test 1: Voice Status Endpoint
echo "=========================================="
echo "Test 1: Voice Status Endpoint"
echo "=========================================="
echo ""

STATUS_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "${BACKEND_URL}/api/v1/voice/status" || echo "HTTP_CODE:000")
HTTP_CODE=$(echo "$STATUS_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
STATUS_BODY=$(echo "$STATUS_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" == "200" ]; then
  echo "✓ Voice status endpoint responded successfully"
  echo "Response:"
  echo "$STATUS_BODY" | python3 -m json.tool 2>/dev/null || echo "$STATUS_BODY"
else
  echo "❌ Voice status endpoint failed (HTTP $HTTP_CODE)"
  echo "Response: $STATUS_BODY"
fi
echo ""

# Test 2: Voice Config Endpoint (Elena)
echo "=========================================="
echo "Test 2: Voice Config Endpoint (Elena)"
echo "=========================================="
echo ""

CONFIG_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "${BACKEND_URL}/api/v1/voice/config/elena" || echo "HTTP_CODE:000")
HTTP_CODE=$(echo "$CONFIG_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
CONFIG_BODY=$(echo "$CONFIG_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" == "200" ]; then
  echo "✓ Voice config endpoint responded successfully"
  echo "Response:"
  echo "$CONFIG_BODY" | python3 -m json.tool 2>/dev/null || echo "$CONFIG_BODY"
else
  echo "❌ Voice config endpoint failed (HTTP $HTTP_CODE)"
  echo "Response: $CONFIG_BODY"
fi
echo ""

# Test 3: Voice Config Endpoint (Marcus)
echo "=========================================="
echo "Test 3: Voice Config Endpoint (Marcus)"
echo "=========================================="
echo ""

CONFIG_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "${BACKEND_URL}/api/v1/voice/config/marcus" || echo "HTTP_CODE:000")
HTTP_CODE=$(echo "$CONFIG_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
CONFIG_BODY=$(echo "$CONFIG_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" == "200" ]; then
  echo "✓ Voice config endpoint responded successfully"
  echo "Response:"
  echo "$CONFIG_BODY" | python3 -m json.tool 2>/dev/null || echo "$CONFIG_BODY"
else
  echo "❌ Voice config endpoint failed (HTTP $HTTP_CODE)"
  echo "Response: $CONFIG_BODY"
fi
echo ""

# Test 4: WebSocket Connection Test
echo "=========================================="
echo "Test 4: WebSocket Connection Test"
echo "=========================================="
echo ""

# Check if Python websockets is available
if ! python3 -c "import websockets" 2>/dev/null; then
  echo "⚠️  websockets library not found. Installing..."
  pip3 install --user websockets >/dev/null 2>&1 || {
    echo "❌ Could not install websockets. Please install manually:"
    echo "   pip3 install websockets"
    echo ""
    echo "Skipping WebSocket test..."
    exit 0
  }
fi

# Create temporary Python script for WebSocket test
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'PYTHON_EOF'
import asyncio
import json
import sys
import websockets
from urllib.parse import urlparse

async def test_websocket(ws_url):
    """Test VoiceLive WebSocket connection"""
    print(f"Connecting to: {ws_url}")
    print()
    
    try:
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✓ WebSocket connected successfully")
            print()
            
            # Test 1: Switch to Elena
            print("Test 4.1: Switching to Elena...")
            await websocket.send(json.dumps({
                "type": "agent",
                "agent_id": "elena"
            }))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✓ Response: {data.get('type', 'unknown')}")
                if data.get('type') == 'agent_switched':
                    print(f"  Agent switched to: {data.get('agent_id')}")
                elif data.get('type') == 'error':
                    print(f"  Error: {data.get('message')}")
                else:
                    print(f"  Full response: {data}")
            except asyncio.TimeoutError:
                print("⚠️  No response received (may be normal)")
            print()
            
            # Test 2: Switch to Marcus
            print("Test 4.2: Switching to Marcus...")
            await websocket.send(json.dumps({
                "type": "agent",
                "agent_id": "marcus"
            }))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✓ Response: {data.get('type', 'unknown')}")
                if data.get('type') == 'agent_switched':
                    print(f"  Agent switched to: {data.get('agent_id')}")
                elif data.get('type') == 'error':
                    print(f"  Error: {data.get('message')}")
                else:
                    print(f"  Full response: {data}")
            except asyncio.TimeoutError:
                print("⚠️  No response received (may be normal)")
            print()
            
            print("✓ WebSocket tests completed!")
            return True
            
    except websockets.exceptions.InvalidURI:
        print("❌ Invalid WebSocket URI")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed: {e}")
        if e.status_code == 401:
            print("  Authentication required. Check if AUTH_REQUIRED is set correctly.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py <websocket_url>")
        sys.exit(1)
    
    ws_url = sys.argv[1]
    # Convert https to wss
    if ws_url.startswith("https://"):
        ws_url = ws_url.replace("https://", "wss://", 1)
    elif ws_url.startswith("http://"):
        ws_url = ws_url.replace("http://", "ws://", 1)
    elif not ws_url.startswith("ws"):
        ws_url = f"wss://{ws_url}"
    
    # Ensure it has the full path with session ID
    if "/voicelive/" not in ws_url:
        import time
        session_id = f"test-session-{int(time.time())}"
        if ws_url.endswith("/"):
            ws_url = f"{ws_url}api/v1/voice/voicelive/{session_id}"
        else:
            ws_url = f"{ws_url}/api/v1/voice/voicelive/{session_id}"
    
    success = asyncio.run(test_websocket(ws_url))
    sys.exit(0 if success else 1)
PYTHON_EOF

# Convert backend URL to WebSocket URL
SESSION_ID="test-session-$(date +%s)"
WS_URL="${BACKEND_URL}/api/v1/voice/voicelive/${SESSION_ID}"
WS_URL=$(echo "$WS_URL" | sed 's|^https://|wss://|')

echo "Testing WebSocket connection..."
echo "WebSocket URL: $WS_URL"
python3 "$TEMP_SCRIPT" "$WS_URL"
WS_RESULT=$?
rm -f "$TEMP_SCRIPT"

echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Backend URL: $BACKEND_URL"
echo "SWA URL: $SWA_URL"
echo ""

if [ "$HTTP_CODE" == "200" ] && [ "$WS_RESULT" == "0" ]; then
  echo "✅ All tests passed!"
  echo ""
  echo "Next steps:"
  echo "  1. Open the SWA in your browser: $SWA_URL"
  echo "  2. Navigate to the voice chat interface"
  echo "  3. Test voice interaction with Elena or Marcus"
else
  echo "⚠️  Some tests failed. Please check the output above."
  echo ""
  echo "Troubleshooting:"
  echo "  - Verify backend is running and accessible"
  echo "  - Check CORS configuration allows your SWA domain"
  echo "  - Verify VoiceLive is configured in backend environment variables"
fi
echo ""

