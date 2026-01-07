#!/usr/bin/env python3
"""
Validate VoiceLive token generation on Azure dev environment.

This script:
1. Discovers the Azure backend URL
2. Tests token generation endpoint
3. Validates failsafe strategies
4. Tests with Managed Identity (if available)

Usage:
    python scripts/validate-token-generation-azure.py [--resource-group engram-rg] [--environment staging]
"""

import asyncio
import argparse
import json
import sys
import subprocess
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from azure.identity import DefaultAzureCredential


async def get_backend_url(resource_group: str, environment: str) -> str:
    """Get backend API URL from Azure."""
    try:
        # Try to get Container App URL
        result = subprocess.run(
            [
                "az", "containerapp", "show",
                "--name", f"{environment}-env-api",
                "--resource-group", resource_group,
                "--query", "properties.configuration.ingress.fqdn",
                "--output", "tsv"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        fqdn = result.stdout.strip()
        if fqdn and fqdn != "None":
            return f"https://{fqdn}"
    except subprocess.CalledProcessError:
        pass
    
    # Fallback to known URL
    if environment == "staging":
        return "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
    elif environment == "dev":
        return "https://dev-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
    else:
        return f"https://{environment}-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io"


async def test_token_generation(
    backend_url: str,
    agent_id: str = "elena",
    modalities: list[str] = None,
    use_auth: bool = False
) -> dict:
    """Test token generation endpoint."""
    if modalities is None:
        modalities = ["video", "text"]
    
    print("=" * 70)
    print("VoiceLive Token Generation Validation (Azure Dev Environment)")
    print("=" * 70)
    print()
    print(f"Backend URL: {backend_url}")
    print(f"Agent: {agent_id}")
    print(f"Modalities: {', '.join(modalities)}")
    print()
    
    # Prepare request
    url = f"{backend_url}/api/v1/voice/realtime/token"
    payload = {
        "agent_id": agent_id,
        "modalities": modalities
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authentication if requested
    if use_auth:
        try:
            credential = DefaultAzureCredential()
            token = credential.get_token("https://ai.azure.com/.default").token
            headers["Authorization"] = f"Bearer {token}"
            print("✅ Using Managed Identity authentication")
        except Exception as e:
            print(f"⚠️  Managed Identity failed: {e}")
            print("   Continuing without authentication...")
    
    print()
    print("Test 1: Token Generation Endpoint")
    print("-" * 70)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Token generation successful!")
                print()
                print("Token Details:")
                print(f"  Token (first 50 chars): {data.get('token', '')[:50]}...")
                print(f"  Token length: {len(data.get('token', ''))} characters")
                print(f"  Endpoint: {data.get('endpoint', 'N/A')}")
                if data.get('expires_at'):
                    print(f"  Expires at: {data.get('expires_at')}")
                print()
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "token_length": len(data.get('token', '')),
                    "endpoint": data.get('endpoint'),
                    "has_token": bool(data.get('token')),
                }
            else:
                error_text = response.text
                print(f"❌ Token generation failed")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {error_text[:500]}")
                print()
                
                # Try to parse JSON error
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_text)
                    print(f"   Error detail: {error_detail}")
                except:
                    pass
                
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": error_text[:500],
                }
                
    except httpx.TimeoutException:
        print("❌ Request timed out")
        return {"success": False, "error": "Timeout"}
    except httpx.RequestError as e:
        print(f"❌ Request error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_health_endpoint(backend_url: str) -> bool:
    """Test health endpoint to verify backend is accessible."""
    print("Test 0: Health Check")
    print("-" * 70)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{backend_url}/health")
            
            if response.status_code == 200:
                print(f"✅ Health check passed ({response.status_code})")
                print()
                return True
            else:
                print(f"⚠️  Health check returned {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                print()
                return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print()
        return False


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate VoiceLive token generation on Azure dev environment"
    )
    
    parser.add_argument(
        "--resource-group",
        default="engram-rg",
        help="Azure resource group (default: engram-rg)"
    )
    
    parser.add_argument(
        "--environment",
        default="staging",
        choices=["staging", "dev", "production"],
        help="Environment to test (default: staging)"
    )
    
    parser.add_argument(
        "--agent",
        default="elena",
        choices=["elena", "marcus", "sage"],
        help="Agent ID (default: elena)"
    )
    
    parser.add_argument(
        "--modalities",
        default="video,text",
        help="Comma-separated modalities (default: video,text)"
    )
    
    parser.add_argument(
        "--use-auth",
        action="store_true",
        help="Use Managed Identity authentication"
    )
    
    parser.add_argument(
        "--backend-url",
        help="Override backend URL (skips Azure discovery)"
    )
    
    args = parser.parse_args()
    
    # Parse modalities
    modalities = [m.strip() for m in args.modalities.split(",")]
    
    # Get backend URL
    if args.backend_url:
        backend_url = args.backend_url.rstrip('/')
    else:
        print("Discovering backend URL from Azure...")
        backend_url = await get_backend_url(args.resource_group, args.environment)
        print(f"✅ Backend URL: {backend_url}")
        print()
    
    # Test health first
    health_ok = await test_health_endpoint(backend_url)
    if not health_ok:
        print("⚠️  Health check failed, but continuing with token test...")
        print()
    
    # Test token generation
    result = await test_token_generation(
        backend_url=backend_url,
        agent_id=args.agent,
        modalities=modalities,
        use_auth=args.use_auth
    )
    
    # Summary
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    print()
    
    if result.get("success"):
        print("✅ Token generation validation PASSED")
        print(f"   Token length: {result.get('token_length')} characters")
        print(f"   Endpoint: {result.get('endpoint')}")
        print()
        print("Next steps:")
        print("  1. Test WebSocket connection with this token")
        print("  2. Verify video connection works")
        print("  3. Check backend logs for strategy usage")
        sys.exit(0)
    else:
        print("❌ Token generation validation FAILED")
        print(f"   Status: {result.get('status_code', 'N/A')}")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print()
        print("Troubleshooting:")
        print("  1. Check backend logs: az containerapp logs show --name <app> --resource-group <rg>")
        print("  2. Verify Managed Identity is configured")
        print("  3. Check AZURE_VOICELIVE_KEY is set (if using API key fallback)")
        print("  4. Verify endpoint URL is correct")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

