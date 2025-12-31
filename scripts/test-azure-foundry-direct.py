#!/usr/bin/env python3
"""
Test Azure AI Foundry endpoint directly to verify configuration.

Tests both API versions and endpoint formats to identify the issue.
"""

import httpx
import json
import sys

# Configuration from user
ENDPOINT = "https://zimax-gw.azure-api.net/zimax"
API_KEY = "cf23c3ed0f9d420dbd02c1e95a5b5bb3"
DEPLOYMENT = "gpt-5.1-chat"

# API versions to test
API_VERSIONS = [
    "2024-05-01-preview",  # User's current
    "2024-12-01-preview",  # Required for gpt-5.1-chat
]

# Endpoint formats to test
FORMATS = [
    "azure",  # /openai/deployments/{deployment}/chat/completions
    "openai",  # /openai/v1/chat/completions (with model in body)
]


def test_endpoint_format(format_type: str, api_version: str):
    """Test a specific endpoint format and API version."""
    
    if format_type == "azure":
        # Azure AI Foundry format
        url = f"{ENDPOINT}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={api_version}"
        payload = {
            "messages": [
                {"role": "user", "content": "Say hi"}
            ],
            "temperature": 0.7,
            "max_tokens": 100,
        }
    else:  # openai
        # OpenAI-compatible format
        url = f"{ENDPOINT}/openai/v1/chat/completions?api-version={api_version}"
        payload = {
            "model": DEPLOYMENT,
            "messages": [
                {"role": "user", "content": "Say hi"}
            ],
            "temperature": 0.7,
            "max_tokens": 100,
        }
    
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
    }
    
    print(f"\n{'='*70}")
    print(f"Testing: {format_type.upper()} format, API version {api_version}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ SUCCESS!")
                print(f"Response: {content[:200]}")
                if len(content) > 200:
                    print(f"... (truncated)")
                return True
            else:
                print(f"❌ FAILED")
                try:
                    error_data = response.json()
                    print(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error: {response.text[:500]}")
                return False
                
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def main():
    print("="*70)
    print("Azure AI Foundry Endpoint Test")
    print("="*70)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Deployment: {DEPLOYMENT}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
    print()
    
    results = {}
    
    # Test all combinations
    for format_type in FORMATS:
        for api_version in API_VERSIONS:
            key = f"{format_type}_{api_version}"
            results[key] = test_endpoint_format(format_type, api_version)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for key, success in results.items():
        format_type, api_version = key.split("_", 1)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {format_type.upper()} format, API {api_version}")
    
    print()
    
    # Recommendations
    working = [k for k, v in results.items() if v]
    if working:
        print("✅ Working configurations:")
        for key in working:
            format_type, api_version = key.split("_", 1)
            print(f"   - {format_type.upper()} format with API version {api_version}")
    else:
        print("❌ No working configurations found!")
        print("   Check:")
        print("   - API key is valid")
        print("   - Endpoint URL is correct")
        print("   - Deployment name is correct")
        print("   - Network connectivity")
    
    sys.exit(0 if working else 1)


if __name__ == "__main__":
    main()

