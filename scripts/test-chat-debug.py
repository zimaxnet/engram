#!/usr/bin/env python3
"""
Enhanced Chat Test Script with Detailed Debugging

Tests chat endpoint and shows detailed error information for troubleshooting.
"""

import os
import sys
import json
import argparse
from typing import Optional

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    sys.exit(1)

API_URL = os.getenv("VITE_API_URL", "https://api.engram.work")


def test_chat_debug(token: Optional[str] = None, message: str = "hi", agent_id: str = "elena"):
    """Test chat endpoint with detailed debugging."""
    url = f"{API_URL}/api/v1/chat"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print(f"🔐 Using token: {token[:20]}...{token[-10:]}")
    else:
        print("⚠️  No token provided - will test without authentication")
    
    payload = {
        "content": message,
        "agent_id": agent_id,
    }
    
    print("=" * 70)
    print("Chat Endpoint Debug Test")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Agent: {agent_id}")
    print(f"Message: {message}")
    print(f"Token: {'Provided' if token else 'Not provided'}")
    print()
    
    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            print("📤 Sending request...")
            print(f"   Headers: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in headers.items()}, indent=2)}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            print()
            
            response = client.post(url, headers=headers, json=payload)
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            print()
            
            # Try to parse response
            try:
                response_data = response.json()
                print("📄 Response Body (JSON):")
                print(json.dumps(response_data, indent=2))
            except json.JSONDecodeError:
                print("📄 Response Body (Text):")
                print(response.text[:1000])
            
            print()
            
            # Detailed analysis
            if response.status_code == 200:
                print("✅ SUCCESS!")
                if isinstance(response_data, dict):
                    content = response_data.get("content", "")
                    if "I apologize, but I encountered an issue" in content:
                        print()
                        print("⚠️  WARNING: Response contains error message!")
                        print("   This means the request succeeded but agent execution failed.")
                        print("   Check backend logs for:")
                        print("     - 'Agent execution failed'")
                        print("     - 'FoundryChatClient: Error calling LLM'")
                        print("     - Full traceback")
                    else:
                        print(f"   Response: {content[:200]}")
            elif response.status_code == 401:
                print("❌ 401 UNAUTHORIZED")
                print()
                print("Authentication failed. Possible causes:")
                print("  1. Token missing or invalid")
                print("  2. Token expired")
                print("  3. Token missing required scopes")
                print("  4. Backend AUTH_REQUIRED=true but no token provided")
                print()
                if token:
                    print("Token provided but still 401 - check:")
                    print("  - Token is valid JWT format")
                    print("  - Token not expired")
                    print("  - Token has correct audience (api://{CLIENT_ID})")
            elif response.status_code == 400:
                print("❌ 400 BAD REQUEST")
                print()
                print("Request validation failed. Check:")
                print("  - Request payload format")
                print("  - Required fields present")
                print("  - CORS preflight (if browser)")
            elif response.status_code == 500:
                print("❌ 500 INTERNAL SERVER ERROR")
                print()
                print("Backend error. Check backend logs for:")
                print("  - 'Agent execution failed'")
                print("  - 'Full traceback'")
                print("  - LLM API errors")
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
            
            return response.status_code == 200
            
    except httpx.TimeoutException:
        print("❌ TIMEOUT: Request took too long (>60s)")
        print("   This suggests:")
        print("   - LLM API call is hanging")
        print("   - Memory operations timing out")
        print("   - Network connectivity issues")
        return False
    except httpx.ConnectError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print(f"   Cannot connect to {url}")
        print("   Check:")
        print("   - API URL is correct")
        print("   - Backend is running and accessible")
        print("   - Network connectivity")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    global API_URL
    
    parser = argparse.ArgumentParser(description="Enhanced chat test with debugging")
    parser.add_argument("--token", help="JWT token (optional - will test without if not provided)")
    parser.add_argument("--message", default="hi", help="Chat message")
    parser.add_argument("--agent", default="elena", help="Agent ID")
    parser.add_argument("--url", help=f"API URL (default: {API_URL})")
    
    args = parser.parse_args()
    
    if args.url:
        API_URL = args.url
    
    # Get token from env if not provided
    token = args.token or os.getenv("AUTH_TOKEN")
    
    success = test_chat_debug(token, args.message, args.agent)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

