#!/usr/bin/env python3
"""
Quick Chat Test Script

Test chat endpoint directly from command line without waiting for deployments.
Get token from browser DevTools and run:

    export AUTH_TOKEN='your-token-here'
    python3 scripts/test-chat-quick.py

Or pass token as argument:

    python3 scripts/test-chat-quick.py --token 'your-token-here'
"""

import os
import sys
import argparse
import json
from pathlib import Path

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    sys.exit(1)

# Default API URL
API_URL = os.getenv("VITE_API_URL", "https://api.engram.work")


def get_token():
    """Get token from environment or argument."""
    token = os.getenv("AUTH_TOKEN")
    if not token:
        print("❌ AUTH_TOKEN not set")
        print("\nTo get token:")
        print("  1. Login via Google in browser")
        print("  2. Open DevTools (F12)")
        print("  3. Go to Application > Local Storage")
        print("  4. Find MSAL token (msal.{clientId}.idtoken)")
        print("  5. Copy token value")
        print("\nThen run:")
        print("  export AUTH_TOKEN='your-token-here'")
        print("  python3 scripts/test-chat-quick.py")
        print("\nOr pass as argument:")
        print("  python3 scripts/test-chat-quick.py --token 'your-token-here'")
        sys.exit(1)
    return token


def test_chat(token: str, message: str = "Hello, this is a test", agent_id: str = "elena"):
    """Test chat endpoint."""
    url = f"{API_URL}/api/v1/chat"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "content": message,
        "agent_id": agent_id,
    }
    
    print("=" * 60)
    print("Chat Test")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Agent: {agent_id}")
    print(f"Message: {message}")
    print()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            print("📤 Sending request...")
            response = client.post(url, headers=headers, json=payload)
            
            print(f"📥 Response Status: {response.status_code}")
            print()
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ SUCCESS!")
                    print()
                    print("Response:")
                    print(json.dumps(data, indent=2))
                    return True
                except json.JSONDecodeError:
                    print("✅ SUCCESS (non-JSON response)")
                    print(f"Response: {response.text[:500]}")
                    return True
            elif response.status_code == 401:
                print("❌ 401 UNAUTHORIZED")
                print()
                try:
                    error = response.json()
                    print("Error details:")
                    print(json.dumps(error, indent=2))
                except:
                    print(f"Error: {response.text[:500]}")
                print()
                print("Possible issues:")
                print("  - Token expired (get fresh token)")
                print("  - Token format incorrect")
                print("  - Token missing required scopes")
                print("  - Backend authentication middleware issue")
                return False
            elif response.status_code == 400:
                print("❌ 400 BAD REQUEST")
                print()
                try:
                    error = response.json()
                    print("Error details:")
                    print(json.dumps(error, indent=2))
                except:
                    print(f"Error: {response.text[:500]}")
                print()
                print("Possible issues:")
                print("  - Invalid request payload")
                print("  - Missing required fields")
                print("  - CORS preflight issue")
                return False
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
                print()
                try:
                    error = response.json()
                    print("Error details:")
                    print(json.dumps(error, indent=2))
                except:
                    print(f"Response: {response.text[:500]}")
                return False
                
    except httpx.TimeoutException:
        print("❌ TIMEOUT: Request took too long (>30s)")
        print("   Check if backend is running and accessible")
        return False
    except httpx.ConnectError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print(f"   Cannot connect to {url}")
        print("   Check if API URL is correct and backend is running")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    global API_URL
    
    parser = argparse.ArgumentParser(description="Quick chat test script")
    parser.add_argument("--token", help="Authentication token (or set AUTH_TOKEN env var)")
    parser.add_argument("--message", default="Hello, this is a test", help="Chat message to send")
    parser.add_argument("--agent", default="elena", help="Agent ID (elena, marcus, sage)")
    parser.add_argument("--url", help=f"API URL (default: {API_URL})")
    
    args = parser.parse_args()
    
    # Override API URL if provided
    if args.url:
        API_URL = args.url
    
    # Get token
    token = args.token or get_token()
    
    # Test chat
    success = test_chat(token, args.message, args.agent)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

