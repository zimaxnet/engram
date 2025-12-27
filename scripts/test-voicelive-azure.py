#!/usr/bin/env python3
"""
Test VoiceLive on Azure Static Web App Deployment

This script tests voice live functionality on the deployed Azure environment:
- Voice status endpoint
- Voice config endpoints (Elena and Marcus)
- WebSocket connection for real-time voice interaction
"""

import asyncio
import json
import sys
import time
import subprocess
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    print("✗ httpx not installed")
    print("Install with: pip install httpx")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("⚠️  websockets not installed (WebSocket tests will be skipped)")
    print("Install with: pip install websockets")
    websockets = None


def get_azure_resource(resource_type, name, resource_group, query):
    """Get Azure resource information using Azure CLI"""
    try:
        result = subprocess.run(
            [
                "az", resource_type, "show",
                "--name", name,
                "--resource-group", resource_group,
                "--query", query,
                "-o", "tsv"
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        output = result.stdout.strip()
        return output if output and output != "null" else None
    except Exception:
        # Catch all exceptions (TimeoutExpired, CalledProcessError, FileNotFoundError, etc.)
        return None


def get_backend_url(resource_group="engram-rg", environment="staging"):
    """Get backend API URL from Azure"""
    # Try environment-specific name first
    url = get_azure_resource(
        "containerapp",
        f"{environment}-env-api",
        resource_group,
        "properties.configuration.ingress.fqdn"
    )
    
    if not url:
        # Try alternative name
        url = get_azure_resource(
            "containerapp",
            "engram-api",
            resource_group,
            "properties.configuration.ingress.fqdn"
        )
    
    if url:
        return f"https://{url}"
    return None


def get_swa_url(resource_group="engram-rg", environment="staging"):
    """Get Static Web App URL from Azure"""
    url = get_azure_resource(
        "staticwebapp",
        f"{environment}-env-web",
        resource_group,
        "properties.defaultHostname"
    )
    
    if not url or url == "null":
        # Try alternative name
        url = get_azure_resource(
            "staticwebapp",
            "engram-web",
            resource_group,
            "properties.defaultHostname"
        )
    
    if url and url != "null":
        return f"https://{url}"
    
    # Fallback to known custom domain
    return "https://engram.work"


async def test_voice_status(backend_url):
    """Test voice status endpoint"""
    print("=" * 60)
    print("Test 1: Voice Status Endpoint")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{backend_url}/api/v1/voice/status")
            
            if response.status_code == 200:
                print("✓ Voice status endpoint responded successfully")
                print("Response:")
                try:
                    data = response.json()
                    print(json.dumps(data, indent=2))
                except:
                    print(response.text)
                return True
            else:
                print(f"❌ Voice status endpoint failed (HTTP {response.status_code})")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing voice status: {e}")
        return False


async def test_voice_config(backend_url, agent_id):
    """Test voice config endpoint for an agent"""
    print("=" * 60)
    print(f"Test 2: Voice Config Endpoint ({agent_id.capitalize()})")
    print("=" * 60)
    print()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{backend_url}/api/v1/voice/config/{agent_id}")
            
            if response.status_code == 200:
                print(f"✓ Voice config endpoint responded successfully for {agent_id}")
                print("Response:")
                try:
                    data = response.json()
                    print(json.dumps(data, indent=2))
                except:
                    print(response.text)
                return True
            else:
                print(f"❌ Voice config endpoint failed (HTTP {response.status_code})")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error testing voice config: {e}")
        return False


async def test_websocket(backend_url):
    """Test VoiceLive WebSocket connection"""
    if not websockets:
        print("⚠️  Skipping WebSocket test (websockets library not installed)")
        return False
    
    print("=" * 60)
    print("Test 3: WebSocket Connection Test")
    print("=" * 60)
    print()
    
    # Convert https to wss
    ws_url = backend_url.replace("https://", "wss://").replace("http://", "ws://")
    session_id = f"test-session-{int(time.time())}"
    ws_url = f"{ws_url}/api/v1/voice/voicelive/{session_id}"
    
    print(f"Connecting to: {ws_url}")
    print()
    
    try:
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✓ WebSocket connected successfully")
            print()
            
            # Test 1: Switch to Elena
            print("Test 3.1: Switching to Elena...")
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
                    print(f"  Full response: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("⚠️  No response received (may be normal)")
            print()
            
            # Test 2: Switch to Marcus
            print("Test 3.2: Switching to Marcus...")
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
                    print(f"  Full response: {json.dumps(data, indent=2)}")
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


async def main():
    """Main test function"""
    print("=" * 60)
    print("Testing VoiceLive on Azure Deployment")
    print("=" * 60)
    print()
    
    # Get configuration
    resource_group = sys.argv[1] if len(sys.argv) > 1 else "engram-rg"
    environment = sys.argv[2] if len(sys.argv) > 2 else "staging"
    
    print(f"Resource Group: {resource_group}")
    print(f"Environment: {environment}")
    print()
    
    # Get URLs
    print("Getting backend URL from Azure...")
    backend_url = get_backend_url(resource_group, environment)
    
    if not backend_url:
        print("❌ Could not get backend URL from Azure.")
        print("   Please provide it manually:")
        print("   python3 scripts/test-voicelive-azure.py <resource_group> <environment> <backend_url>")
        if len(sys.argv) > 3:
            backend_url = sys.argv[3]
            print(f"   Using provided URL: {backend_url}")
        else:
            sys.exit(1)
    
    print(f"✓ Backend URL: {backend_url}")
    
    swa_url = get_swa_url(resource_group, environment)
    print(f"✓ SWA URL: {swa_url}")
    print()
    
    # Run tests
    results = []
    
    # Test 1: Voice Status
    result1 = await test_voice_status(backend_url)
    results.append(("Voice Status", result1))
    print()
    
    # Test 2: Voice Config (Elena)
    result2 = await test_voice_config(backend_url, "elena")
    results.append(("Voice Config (Elena)", result2))
    print()
    
    # Test 3: Voice Config (Marcus)
    result3 = await test_voice_config(backend_url, "marcus")
    results.append(("Voice Config (Marcus)", result3))
    print()
    
    # Test 4: WebSocket
    result4 = await test_websocket(backend_url)
    results.append(("WebSocket Connection", result4))
    print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    print(f"Backend URL: {backend_url}")
    print(f"SWA URL: {swa_url}")
    print()
    
    all_passed = all(result for _, result in results)
    
    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    print()
    
    if all_passed:
        print("✅ All tests passed!")
        print()
        print("Next steps:")
        print(f"  1. Open the SWA in your browser: {swa_url}")
        print("  2. Navigate to the voice chat interface")
        print("  3. Test voice interaction with Elena or Marcus")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        print()
        print("Troubleshooting:")
        print("  - Verify backend is running and accessible")
        print("  - Check CORS configuration allows your SWA domain")
        print("  - Verify VoiceLive is configured in backend environment variables")
        print("  - Check Azure Container App logs for errors")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())

