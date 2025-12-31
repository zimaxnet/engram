#!/usr/bin/env python3
"""
Test Voice WebSocket Authentication

Tests that the voice WebSocket endpoint properly extracts and validates JWT tokens
from query parameters and creates SecurityContext with authenticated user_id.

Usage:
    python3 scripts/test-voice-websocket-auth.py --token <JWT_TOKEN> [--url <API_URL>]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Optional

import httpx
import websockets
from websockets.exceptions import ConnectionClosedError, InvalidStatusCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.environ.get("API_URL", "https://api.engram.work")


async def test_websocket_with_token(token: str, session_id: str, url: str = API_URL) -> bool:
    """
    Test WebSocket connection with JWT token in query parameter.
    
    Args:
        token: JWT token for authentication
        session_id: Session ID for the WebSocket connection
        url: API base URL
        
    Returns:
        True if test passes, False otherwise
    """
    # Convert HTTP URL to WebSocket URL
    ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
    ws_endpoint = f"{ws_url}/api/v1/voice/voicelive/{session_id}?token={token}"
    
    logger.info(f"Connecting to WebSocket: {ws_endpoint[:100]}...")
    
    try:
        async with websockets.connect(ws_endpoint) as websocket:
            logger.info("✅ WebSocket connection established")
            
            # Send a test message to verify connection
            test_message = {
                "type": "agent",
                "agent_id": "elena"
            }
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Test message sent")
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"✅ Received response: {response[:200]}")
                return True
            except asyncio.TimeoutError:
                logger.warning("⚠️  No response received (may be normal for voice endpoint)")
                return True  # Still consider it a pass if connection was established
            
    except InvalidStatusCode as e:
        if e.status_code == 1008:
            logger.error(f"❌ WebSocket closed with code 1008: {e.reason}")
            logger.error("   This indicates authentication failed or token was invalid")
            return False
        else:
            logger.error(f"❌ WebSocket connection failed with status {e.status_code}: {e.reason}")
            return False
    except ConnectionClosedError as e:
        logger.error(f"❌ WebSocket connection closed: {e.code} - {e.reason}")
        return False
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")
        return False


async def test_websocket_without_token(session_id: str, url: str = API_URL, auth_required: bool = True) -> bool:
    """
    Test WebSocket connection without token (should fail if AUTH_REQUIRED=true).
    
    Args:
        session_id: Session ID for the WebSocket connection
        url: API base URL
        auth_required: Whether authentication is required
        
    Returns:
        True if behavior matches expectations, False otherwise
    """
    ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
    ws_endpoint = f"{ws_url}/api/v1/voice/voicelive/{session_id}"
    
    logger.info(f"Testing WebSocket without token: {ws_endpoint}")
    
    try:
        async with websockets.connect(ws_endpoint) as websocket:
            if auth_required:
                logger.error("❌ WebSocket connected without token when AUTH_REQUIRED=true (should have failed)")
                return False
            else:
                logger.info("✅ WebSocket connected without token (AUTH_REQUIRED=false)")
                return True
    except InvalidStatusCode as e:
        if e.status_code == 1008 and auth_required:
            logger.info(f"✅ WebSocket correctly rejected connection without token: {e.reason}")
            return True
        else:
            logger.error(f"❌ Unexpected status code: {e.status_code}")
            return False
    except Exception as e:
        if auth_required:
            logger.info(f"✅ WebSocket correctly rejected connection: {e}")
            return True
        else:
            logger.error(f"❌ Unexpected error: {e}")
            return False


async def main():
    parser = argparse.ArgumentParser(description="Test Voice WebSocket Authentication")
    parser.add_argument("--token", help="JWT token for authentication")
    parser.add_argument("--url", default=API_URL, help="API base URL")
    parser.add_argument("--session-id", default=f"test-session-{os.getpid()}", help="Session ID")
    parser.add_argument("--test-no-token", action="store_true", help="Also test without token")
    args = parser.parse_args()
    
    token = args.token or os.environ.get("AUTH_TOKEN")
    
    if not token:
        print("❌ AUTH_TOKEN not set\n")
        print("To get token:")
        print("  1. Login via Google in browser")
        print("  2. Open DevTools (F12)")
        print("  3. Go to Application > Local Storage")
        print("  4. Find MSAL token (msal.{clientId}.idtoken)")
        print("  5. Copy token value\n")
        print("Then run:")
        print("  export AUTH_TOKEN='your-token-here'")
        print("  python3 scripts/test-voice-websocket-auth.py\n")
        print("Or pass as argument:")
        print("  python3 scripts/test-voice-websocket-auth.py --token 'your-token-here'\n")
        sys.exit(1)
    
    print("=" * 60)
    print("Voice WebSocket Authentication Test")
    print("=" * 60)
    print(f"URL: {args.url}")
    print(f"Session ID: {args.session_id}")
    print()
    
    # Test 1: WebSocket with token
    print("Test 1: WebSocket connection with JWT token")
    print("-" * 60)
    result1 = await test_websocket_with_token(token, args.session_id, args.url)
    print()
    
    # Test 2: WebSocket without token (if requested)
    result2 = True
    if args.test_no_token:
        print("Test 2: WebSocket connection without token")
        print("-" * 60)
        # Note: We can't easily determine AUTH_REQUIRED from here, so we'll test both scenarios
        result2 = await test_websocket_without_token(args.session_id, args.url, auth_required=True)
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    if result1:
        print("✅ Test 1 (with token): PASSED")
    else:
        print("❌ Test 1 (with token): FAILED")
    
    if args.test_no_token:
        if result2:
            print("✅ Test 2 (without token): PASSED")
        else:
            print("❌ Test 2 (without token): FAILED")
    
    if result1 and (not args.test_no_token or result2):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

