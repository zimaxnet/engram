#!/usr/bin/env python3
"""
Test Chat Model Router Configuration

This script tests the Model Router configuration for chat to diagnose issues.
Similar to the VoiceLive validation script.
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core import get_settings

async def test_model_router_config():
    """Test Model Router configuration for chat."""
    
    settings = get_settings()
    
    print("=" * 60)
    print("Chat Model Router Configuration Test")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("📋 Environment Variables:")
    print(f"   AZURE_AI_ENDPOINT: {settings.azure_ai_endpoint or '❌ NOT SET'}")
    print(f"   AZURE_AI_MODEL_ROUTER: {settings.azure_ai_model_router or '❌ NOT SET (using direct deployment)'}")
    print(f"   AZURE_AI_DEPLOYMENT: {settings.azure_ai_deployment}")
    print(f"   AZURE_AI_KEY: {'✅ SET' if settings.azure_ai_key else '❌ NOT SET'}")
    print(f"   AZURE_AI_API_VERSION: {settings.azure_ai_api_version}")
    print()
    
    # Validate endpoint format
    if not settings.azure_ai_endpoint:
        print("❌ ERROR: AZURE_AI_ENDPOINT not configured")
        return False
    
    endpoint = settings.azure_ai_endpoint.rstrip('/')
    is_apim = "/openai/v1" in endpoint
    
    print("🔍 Endpoint Analysis:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Type: {'APIM Gateway' if is_apim else 'Foundry Direct'}")
    print()
    
    # Determine deployment name
    deployment = settings.azure_ai_model_router or settings.azure_ai_deployment
    print(f"📦 Deployment: {deployment}")
    if settings.azure_ai_model_router:
        print(f"   ✅ Using Model Router: {deployment}")
    else:
        print(f"   ⚠️  Using direct deployment: {deployment}")
    print()
    
    # Build URL
    if is_apim:
        url = f"{endpoint}/chat/completions"
    else:
        # Foundry format
        if settings.azure_ai_project_name:
            base = f"{endpoint}/api/projects/{settings.azure_ai_project_name}"
        else:
            base = endpoint
        url = f"{base}/openai/deployments/{deployment}/chat/completions?api-version={settings.azure_ai_api_version}"
    
    print("🌐 Request URL:")
    print(f"   {url}")
    print()
    
    # Test API call
    if not settings.azure_ai_key:
        print("❌ ERROR: AZURE_AI_KEY not configured")
        print("   Cannot test API call without authentication")
        return False
    
    print("🧪 Testing API Call...")
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # Add API key header
    if is_apim:
        headers["Ocp-Apim-Subscription-Key"] = settings.azure_ai_key
        headers["api-key"] = settings.azure_ai_key
    else:
        headers["api-key"] = settings.azure_ai_key
    
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, this is a test message. Please respond with 'Test successful'."}
        ]
    }
    
    # Add model for OpenAI-compatible endpoints
    if is_apim:
        payload["model"] = deployment
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"   ✅ SUCCESS!")
                print(f"   Response: {content[:100]}...")
                return True
            else:
                print(f"   ❌ ERROR: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_chat():
    """Test agent chat functionality."""
    print()
    print("=" * 60)
    print("Agent Chat Test")
    print("=" * 60)
    print()
    
    try:
        from backend.agents import chat as agent_chat
        from backend.core import EnterpriseContext, SecurityContext, Role
        
        # Create a test context
        security = SecurityContext(
            user_id="test-user",
            email="test@example.com",
            roles=[Role.ANALYST],
            scopes=["*"]
        )
        
        context = EnterpriseContext.create_new(security)
        
        print("🧪 Testing agent chat with Elena...")
        response, updated_context, agent_id = await agent_chat(
            query="Hello, this is a test. Please respond with 'Test successful'.",
            context=context,
            agent_id="elena"
        )
        
        print(f"   ✅ SUCCESS!")
        print(f"   Agent: {agent_id}")
        print(f"   Response: {response[:200]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    model_router_ok = await test_model_router_config()
    agent_chat_ok = await test_agent_chat()
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"   Model Router Config: {'✅ PASS' if model_router_ok else '❌ FAIL'}")
    print(f"   Agent Chat: {'✅ PASS' if agent_chat_ok else '❌ FAIL'}")
    print()
    
    if not model_router_ok or not agent_chat_ok:
        print("❌ Chat is not working. Check the errors above.")
        print()
        print("Common Issues:")
        print("   1. AZURE_AI_ENDPOINT not set correctly")
        print("   2. AZURE_AI_KEY missing or incorrect")
        print("   3. AZURE_AI_MODEL_ROUTER not set (if using Model Router)")
        print("   4. Model Router deployment name mismatch")
        print("   5. APIM subscription key incorrect")
        return 1
    
    print("✅ Chat is working correctly!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

