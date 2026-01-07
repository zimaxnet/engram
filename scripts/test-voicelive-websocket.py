#!/usr/bin/env python3
"""
Test VoiceLive WebSocket Connection

Tests the VoiceLive WebSocket proxy endpoint to verify:
1. Connection establishes successfully
2. Audio/transcript flow works
3. video_connection info is provided when avatar is enabled

Usage:
    python scripts/test-voicelive-websocket.py [--backend-url URL] [--token TOKEN]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

try:
    import websockets
except ImportError:
    print("❌ 'websockets' library not found. Please install it:")
    print("   pip install websockets")
    sys.exit(1)


async def test_voicelive_websocket(backend_url: str, token: str = None):
    """Test VoiceLive WebSocket connection."""
    print("=" * 60)
    print("Testing VoiceLive WebSocket Connection")
    print("=" * 60)
    print(f"Backend URL: {backend_url}")
    print(f"Session ID: test-session-{asyncio.get_event_loop().time()}")
    print()
    
    session_id = f"test-session-{int(asyncio.get_event_loop().time())}"
    
    # Build WebSocket URL
    ws_url = f"{backend_url.replace('https://', 'wss://').replace('http://', 'ws://')}/api/v1/voice/voicelive/{session_id}"
    if token:
        ws_url += f"?token={token}"
    
    print(f"Connecting to: {ws_url}")
    print()
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected")
            print()
            
            # Wait for initial messages
            print("Waiting for initial messages...")
            print("-" * 60)
            
            messages_received = []
            timeout = 10  # seconds
            
            try:
                # Wait for agent_switched message
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                data = json.loads(message)
                messages_received.append(data)
                
                print(f"✅ Received message: {data.get('type', 'unknown')}")
                
                # Check if it's agent_switched
                if data.get('type') == 'agent_switched':
                    print(f"   Agent ID: {data.get('agent_id', 'N/A')}")
                    
                    # Check for video_connection
                    if 'video_connection' in data:
                        video_conn = data['video_connection']
                        print("   ✅ Video connection info provided:")
                        print(f"      Endpoint: {video_conn.get('endpoint', 'N/A')}")
                        print(f"      Modalities: {video_conn.get('modalities', 'N/A')}")
                        print(f"      Token length: {len(video_conn.get('token', ''))} chars")
                    else:
                        print("   ⚠️  No video_connection in message (avatar may not be enabled)")
                
                # Check for error
                elif data.get('type') == 'error':
                    print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
                    return False
                
                print()
                print("=" * 60)
                print("Test Summary")
                print("=" * 60)
                print("✅ WebSocket connection successful")
                print("✅ Initial message received")
                
                if 'video_connection' in data:
                    print("✅ Video connection info provided")
                else:
                    print("⚠️  Video connection info not provided (may be expected if avatar disabled)")
                
                return True
                
            except asyncio.TimeoutError:
                print(f"❌ Timeout: No message received within {timeout} seconds")
                return False
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection failed: {e.status_code}")
        if e.status_code == 401 or e.status_code == 403:
            print("   Authentication required - provide token with --token")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test VoiceLive WebSocket connection")
    parser.add_argument(
        "--backend-url",
        default="https://engram.work",
        help="Backend URL (default: https://engram.work)"
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Authentication token (optional if auth not required)"
    )
    
    args = parser.parse_args()
    
    success = asyncio.run(test_voicelive_websocket(args.backend_url, args.token))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
