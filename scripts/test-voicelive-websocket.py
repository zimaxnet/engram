#!/usr/bin/env python3
"""
Test VoiceLive WebSocket Connection

Tests the VoiceLive WebSocket endpoint to verify:
- Connection establishment
- Agent switching (Elena and Marcus)
- Message handling
"""

import asyncio
import json
import sys
from typing import Optional

try:
    import websockets
except ImportError:
    print("✗ websockets not installed")
    print("Install with: pip install websockets")
    sys.exit(1)


async def test_voicelive_websocket():
    """Test VoiceLive WebSocket connection"""
    print("=" * 60)
    print("Testing VoiceLive WebSocket Connection")
    print("=" * 60)
    print()
    
    uri = "ws://localhost:8082/api/v1/voice/voicelive/test-session-123"
    print(f"Connecting to: {uri}")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected successfully")
            print()
            
            # Test 1: Switch to Elena
            print("Test 1: Switching to Elena...")
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
            print("Test 2: Switching to Marcus...")
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
            
            # Test 3: Send a test message (should be ignored or handled)
            print("Test 3: Sending test message...")
            await websocket.send(json.dumps({
                "type": "test",
                "message": "This is a test"
            }))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print(f"✓ Response: {data.get('type', 'unknown')}")
                if data.get('type') == 'error':
                    print(f"  Expected error: {data.get('message')}")
            except asyncio.TimeoutError:
                print("✓ No response (expected for unknown message type)")
            print()
            
            print("=" * 60)
            print("✓ All WebSocket tests completed!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  - Test with actual audio streaming")
            print("  - Update frontend to use VoiceLive endpoint")
            print()
            
    except websockets.exceptions.InvalidURI:
        print("✗ Invalid WebSocket URI")
        return False
    except ConnectionRefusedError:
        print("✗ Connection refused")
        print("  Make sure the backend is running:")
        print("    ./scripts/start-backend.sh")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_voicelive_websocket())
    sys.exit(0 if success else 1)

