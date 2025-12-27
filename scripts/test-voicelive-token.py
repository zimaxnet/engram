#!/usr/bin/env python3
"""
Test VoiceLive Token Endpoint Configuration

This script validates the VoiceLive ephemeral token endpoint configuration
by testing the actual Azure OpenAI Realtime API token request.

Usage:
    python3 scripts/test-voicelive-token.py
    
    # Or with environment variables
    AZURE_VOICELIVE_ENDPOINT="https://your-resource.services.ai.azure.com" \
    AZURE_VOICELIVE_KEY="your-key" \
    AZURE_VOICELIVE_MODEL="gpt-realtime" \
    python3 scripts/test-voicelive-token.py
"""

import asyncio
import json
import os
import sys
from typing import Optional

try:
    import httpx
except ImportError:
    print("✗ httpx not installed")
    print("Install with: pip install httpx")
    sys.exit(1)


def detect_endpoint_type(endpoint: str) -> str:
    """Detect if endpoint is unified or direct."""
    endpoint_lower = endpoint.lower().rstrip('/')
    if "services.ai.azure.com" in endpoint_lower:
        return "unified"
    elif "openai.azure.com" in endpoint_lower:
        return "direct"
    else:
        return "unknown"


def build_token_url(endpoint: str, model: str, endpoint_type: str, project_name: Optional[str] = None) -> str:
    """
    Build the correct token URL based on endpoint type.
    
    For unified endpoints:
    - With project: /api/projects/{project}/openai/realtime/client_secrets
    - Without project: /openai/realtime/client_secrets
    
    For direct endpoints:
    - /openai/deployments/{model}/realtime/client_secrets
    """
    endpoint = endpoint.rstrip('/')
    if endpoint_type == "direct":
        return f"{endpoint}/openai/deployments/{model}/realtime/client_secrets"
    else:
        if project_name:
            return f"{endpoint}/api/projects/{project_name}/openai/realtime/client_secrets"
        else:
            return f"{endpoint}/openai/realtime/client_secrets"


async def test_token_endpoint(
    endpoint: str,
    api_key: str,
    model: str,
    agent_id: str = "elena",
    project_name: Optional[str] = None,
    api_version: str = "2024-10-01-preview"
) -> tuple[bool, dict]:
    """
    Test the Azure OpenAI Realtime API token endpoint.
    
    Returns:
        (success: bool, result: dict)
    """
    endpoint_type = detect_endpoint_type(endpoint)
    
    if endpoint_type == "unknown":
        return False, {
            "error": f"Unknown endpoint format: {endpoint}",
            "expected": "services.ai.azure.com or openai.azure.com"
        }
    
    token_url = build_token_url(endpoint, model, endpoint_type, project_name)
    
    # Build session configuration (flattened format)
    session_config = {
        "model": model,
        "modalities": ["audio", "text"],
        "instructions": f"You are {agent_id}, a helpful assistant.",
        "voice": "en-US-Ava:DragonHDLatestNeural" if agent_id == "elena" else "en-US-GuyNeural",
        "input_audio_transcription": {
            "model": "whisper-1"
        },
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.6,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 800,
        },
    }
    
    print(f"Testing token endpoint...")
    print(f"  Endpoint type: {endpoint_type}")
    print(f"  URL: {token_url}")
    print(f"  Model: {model}")
    print(f"  Agent: {agent_id}")
    if project_name:
        print(f"  Project: {project_name}")
    print(f"  API version: {api_version}")
    print()
    
    try:
        # For project-based endpoints, use both headers
        headers = {
            "Content-Type": "application/json",
        }
        if project_name and endpoint_type == "unified":
            headers["Ocp-Apim-Subscription-Key"] = api_key
            headers["api-key"] = api_key
        else:
            headers["api-key"] = api_key
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_url,
                headers=headers,
                params={"api-version": api_version},
                json=session_config,
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("value", "")
                expires_at = data.get("expires_at", "")
                
                if token:
                    return True, {
                        "status": "success",
                        "token_length": len(token),
                        "expires_at": expires_at,
                        "endpoint_type": endpoint_type,
                        "url": token_url
                    }
                else:
                    return False, {
                        "status": "error",
                        "error": "No token in response",
                        "response": data
                    }
            else:
                error_body = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_body)
                except:
                    error_detail = error_body
                
                return False, {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": error_detail,
                    "url": token_url,
                    "endpoint_type": endpoint_type
                }
                
    except httpx.TimeoutException:
        return False, {
            "status": "error",
            "error": "Request timed out after 30 seconds"
        }
    except httpx.RequestError as e:
        return False, {
            "status": "error",
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return False, {
            "status": "error",
            "error": f"Unexpected error: {str(e)}"
        }


async def main():
    """Main test function"""
    print("=" * 60)
    print("VoiceLive Token Endpoint Configuration Test")
    print("=" * 60)
    print()
    
    # Get configuration from environment
    endpoint = os.getenv("AZURE_VOICELIVE_ENDPOINT", "").strip()
    api_key = os.getenv("AZURE_VOICELIVE_KEY", "").strip()
    model = os.getenv("AZURE_VOICELIVE_MODEL", "gpt-realtime").strip()
    project_name = os.getenv("AZURE_VOICELIVE_PROJECT_NAME", "").strip() or None
    api_version = os.getenv("AZURE_VOICELIVE_API_VERSION", "2024-10-01-preview").strip()
    
    if not endpoint:
        print("❌ AZURE_VOICELIVE_ENDPOINT not set")
        print()
        print("Set it with:")
        print("  export AZURE_VOICELIVE_ENDPOINT='https://your-resource.services.ai.azure.com'")
        sys.exit(1)
    
    if not api_key:
        print("❌ AZURE_VOICELIVE_KEY not set")
        print()
        print("Set it with:")
        print("  export AZURE_VOICELIVE_KEY='your-api-key'")
        sys.exit(1)
    
    print("Configuration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Model: {model}")
    if project_name:
        print(f"  Project: {project_name}")
    print(f"  API Version: {api_version}")
    print(f"  API Key: {'*' * min(len(api_key), 8)}...")
    print()
    
    # Test token endpoint
    success, result = await test_token_endpoint(endpoint, api_key, model, project_name=project_name, api_version=api_version)
    
    print("=" * 60)
    print("Test Results")
    print("=" * 60)
    print()
    
    if success:
        print("✅ Token endpoint test PASSED")
        print()
        print("Details:")
        print(f"  Endpoint type: {result.get('endpoint_type')}")
        print(f"  Token URL: {result.get('url')}")
        print(f"  Token length: {result.get('token_length')} characters")
        if result.get('expires_at'):
            print(f"  Expires at: {result.get('expires_at')}")
        print()
        print("✅ VoiceLive token endpoint is correctly configured!")
        return 0
    else:
        print("❌ Token endpoint test FAILED")
        print()
        print("Error details:")
        for key, value in result.items():
            if key != "status":
                print(f"  {key}: {value}")
        print()
        
        # Provide troubleshooting guidance
        if result.get("status_code") == 400:
            print("Troubleshooting 400 Bad Request:")
            print("  1. Verify endpoint URL format:")
            print("     - Unified: https://<resource>.services.ai.azure.com")
            print("     - Direct: https://<resource>.openai.azure.com")
            print("  2. Check request body format (must be flattened)")
            print("  3. Verify API version: 2024-10-01-preview")
            print("  4. Check backend logs for detailed Azure error message")
        elif result.get("status_code") == 401:
            print("Troubleshooting 401 Unauthorized:")
            print("  1. Verify API key is correct")
            print("  2. Check if key has Realtime API permissions")
            print("  3. For Managed Identity, verify RBAC role assignment")
        elif result.get("status_code") == 404:
            print("Troubleshooting 404 Not Found:")
            print("  1. Verify model deployment exists: gpt-realtime")
            print("  2. Check endpoint URL is correct")
            print("  3. Verify deployment name matches model parameter")
        
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

