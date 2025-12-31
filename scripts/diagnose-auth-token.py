#!/usr/bin/env python3
"""
Comprehensive Authentication Token Diagnostic Tool

This script helps diagnose authentication issues by:
1. Decoding and inspecting JWT tokens from Azure CIAM
2. Verifying JWKS endpoint accessibility
3. Testing token signature validation
4. Checking issuer and audience format mismatches
"""

import asyncio
import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from jose import jwt

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.api.middleware.auth import EntraIDAuth
from backend.core import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def decode_token_payload(token: str) -> dict:
    """Decode JWT token without verification (for inspection)"""
    try:
        # Split token into parts
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format - expected 3 parts")
        
        # Decode header and payload (base64url)
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
        
        return {
            'header': header,
            'payload': payload,
            'signature': parts[2][:20] + '...'  # First 20 chars of signature
        }
    except Exception as e:
        logger.error(f"Failed to decode token: {e}")
        raise


def print_token_info(token_data: dict):
    """Print formatted token information"""
    header = token_data['header']
    payload = token_data['payload']
    
    print("\n" + "="*80)
    print("TOKEN INSPECTION")
    print("="*80)
    
    print("\n📋 HEADER:")
    print(f"  Algorithm: {header.get('alg', 'N/A')}")
    print(f"  Key ID: {header.get('kid', 'N/A')}")
    print(f"  Type: {header.get('typ', 'N/A')}")
    
    print("\n📋 PAYLOAD (Claims):")
    print(f"  Issuer (iss): {payload.get('iss', 'N/A')}")
    print(f"  Audience (aud): {payload.get('aud', 'N/A')}")
    print(f"  Tenant ID (tid): {payload.get('tid', 'N/A')}")
    print(f"  Subject (sub): {payload.get('sub', 'N/A')}")
    print(f"  Object ID (oid): {payload.get('oid', 'N/A')}")
    print(f"  Email: {payload.get('email', payload.get('preferred_username', 'N/A'))}")
    print(f"  Name: {payload.get('name', 'N/A')}")
    print(f"  Scopes (scp): {payload.get('scp', 'N/A')}")
    print(f"  Expires (exp): {payload.get('exp', 'N/A')} ({payload.get('exp', 0) - __import__('time').time():.0f}s from now)")
    print(f"  Issued At (iat): {payload.get('iat', 'N/A')}")
    
    # Check for roles
    roles = payload.get('roles', [])
    if roles:
        print(f"  Roles: {', '.join(roles)}")
    else:
        print("  Roles: None (check app registration role assignments)")
    
    print(f"\n🔐 Signature: {token_data['signature']}")


async def test_jwks_endpoints(tenant_id: str, tenant_domain: str, token_tid: Optional[str] = None):
    """Test multiple possible JWKS endpoints"""
    print("\n" + "="*80)
    print("JWKS ENDPOINT TESTING")
    print("="*80)
    
    endpoints = [
        # Named domain endpoint (what we configure)
        f"https://{tenant_domain}.ciamlogin.com/{tenant_id}/discovery/v2.0/keys",
        # GUID-based endpoint (what Azure might actually use)
        f"https://{tenant_id}.ciamlogin.com/{tenant_id}/discovery/v2.0/keys",
    ]
    
    # If we have a token tenant ID, test that too
    if token_tid and token_tid != tenant_id:
        endpoints.append(f"https://{token_tid}.ciamlogin.com/{token_tid}/discovery/v2.0/keys")
        # Also try with named domain but token TID
        endpoints.append(f"https://{tenant_domain}.ciamlogin.com/{token_tid}/discovery/v2.0/keys")
    
    working_endpoints = []
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    jwks = response.json()
                    key_count = len(jwks.get('keys', []))
                    print(f"  ✅ SUCCESS - Found {key_count} keys")
                    working_endpoints.append(endpoint)
                    
                    # Show first key ID
                    if jwks.get('keys'):
                        first_key = jwks['keys'][0]
                        print(f"  First Key ID (kid): {first_key.get('kid', 'N/A')}")
                        print(f"  Key Type: {first_key.get('kty', 'N/A')}")
                else:
                    print(f"  ❌ FAILED - HTTP {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
        except httpx.TimeoutException:
            print(f"  ⏱️  TIMEOUT - Endpoint not reachable")
        except Exception as e:
            print(f"  ❌ ERROR - {e}")
    
    return working_endpoints


async def test_token_validation(token: str, auth: EntraIDAuth):
    """Test token validation using the auth middleware"""
    print("\n" + "="*80)
    print("TOKEN VALIDATION TEST")
    print("="*80)
    
    try:
        # Decode token first to get info
        token_data = decode_token_payload(token)
        payload = token_data['payload']
        
        print(f"\n🔍 Attempting to validate token...")
        print(f"  Token Issuer: {payload.get('iss')}")
        print(f"  Token Audience: {payload.get('aud')}")
        print(f"  Token Tenant ID: {payload.get('tid')}")
        
        # Show what backend expects
        print(f"\n📋 Backend Configuration:")
        print(f"  Expected Client ID: {auth.client_id}")
        print(f"  Expected Tenant ID: {auth.tenant_id}")
        print(f"  Expected Tenant Domain: {auth.tenant_domain}")
        print(f"  JWKS URI: {auth.jwks_uri}")
        print(f"  Valid Issuers: {auth.valid_issuers}")
        
        # Try to validate
        try:
            validated_token = await auth.validate_token(token)
            print(f"\n✅ TOKEN VALIDATION SUCCESSFUL!")
            print(f"  User ID (oid): {validated_token.oid}")
            print(f"  Email: {validated_token.email or validated_token.preferred_username}")
            print(f"  Tenant ID: {validated_token.tid}")
            print(f"  Roles: {validated_token.roles}")
            return True
        except Exception as e:
            print(f"\n❌ TOKEN VALIDATION FAILED!")
            print(f"  Error: {e}")
            print(f"  Error Type: {type(e).__name__}")
            
            # Provide specific guidance
            token_issuer = payload.get('iss')
            token_audience = payload.get('aud')
            token_tid = payload.get('tid')
            
            print(f"\n🔧 DIAGNOSTIC ANALYSIS:")
            
            # Check issuer mismatch
            if token_issuer not in auth.valid_issuers:
                print(f"  ⚠️  ISSUER MISMATCH:")
                print(f"     Token issuer: {token_issuer}")
                print(f"     Expected one of: {auth.valid_issuers}")
                print(f"     Solution: Add token issuer to valid_issuers list")
            
            # Check audience mismatch
            valid_audiences = [auth.client_id, f"api://{auth.client_id}"]
            if token_audience not in valid_audiences:
                print(f"  ⚠️  AUDIENCE MISMATCH:")
                print(f"     Token audience: {token_audience}")
                print(f"     Expected one of: {valid_audiences}")
                print(f"     Solution: Check frontend API scope configuration")
            
            # Check JWKS endpoint
            print(f"\n  🔍 JWKS Endpoint Check:")
            print(f"     Configured: {auth.jwks_uri}")
            print(f"     Token issuer suggests: {token_issuer.replace('/v2.0', '/discovery/v2.0/keys')}")
            
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED TO DECODE TOKEN: {e}")
        return False


async def main():
    """Main diagnostic function"""
    print("="*80)
    print("ENGRAM AUTHENTICATION TOKEN DIAGNOSTIC")
    print("="*80)
    
    # Get token from user or environment
    token = os.environ.get('AUTH_TOKEN')
    
    if not token:
        print("\n📝 No token provided via AUTH_TOKEN environment variable.")
        print("\nTo use this script:")
        print("  1. Get a token from your browser after logging in:")
        print("     - Open browser DevTools (F12)")
        print("     - Go to Application/Storage > Local Storage")
        print("     - Look for MSAL tokens or check Network tab for Authorization header")
        print("  2. Run: AUTH_TOKEN='your-token-here' python3 scripts/diagnose-auth-token.py")
        print("\nAlternatively, paste token when prompted:")
        token = input("\nPaste your JWT token (or press Enter to skip token validation): ").strip()
    
    # Load settings and create auth instance
    settings = get_settings()
    auth = EntraIDAuth()
    
    print("\n" + "="*80)
    print("BACKEND CONFIGURATION")
    print("="*80)
    print(f"Environment: {settings.environment}")
    print(f"Auth Required: {settings.auth_required}")
    print(f"Tenant ID: {auth.tenant_id}")
    print(f"Tenant Domain: {auth.tenant_domain}")
    print(f"Client ID: {auth.client_id}")
    print(f"External ID: {auth._is_external_id}")
    print(f"Authority: {auth.authority}")
    print(f"JWKS URI: {auth.jwks_uri}")
    print(f"Valid Issuers: {auth.valid_issuers}")
    
    # Test JWKS endpoints
    token_tid = None
    if token:
        try:
            token_data = decode_token_payload(token)
            token_tid = token_data['payload'].get('tid')
            print_token_info(token_data)
        except Exception as e:
            print(f"\n⚠️  Could not decode token: {e}")
            print("Continuing with JWKS endpoint tests...")
    
    # Test JWKS endpoints
    working_jwks = await test_jwks_endpoints(
        auth.tenant_id,
        auth.tenant_domain,
        token_tid
    )
    
    if not working_jwks:
        print("\n❌ NO WORKING JWKS ENDPOINTS FOUND!")
        print("This is a critical issue - token validation will fail.")
        print("\nPossible causes:")
        print("  1. Tenant ID or domain is incorrect")
        print("  2. Network connectivity issues")
        print("  3. Azure CIAM tenant not properly configured")
    else:
        print(f"\n✅ Found {len(working_jwks)} working JWKS endpoint(s)")
        if auth.jwks_uri not in working_jwks:
            print(f"\n⚠️  WARNING: Configured JWKS URI is not working!")
            print(f"  Configured: {auth.jwks_uri}")
            print(f"  Working endpoints: {working_jwks}")
            print(f"  Consider updating JWKS URI in auth.py")
    
    # Test token validation if token provided
    if token:
        await test_token_validation(token, auth)
    else:
        print("\n" + "="*80)
        print("SKIPPING TOKEN VALIDATION (no token provided)")
        print("="*80)
        print("\nTo test token validation, provide a token:")
        print("  AUTH_TOKEN='your-token' python3 scripts/diagnose-auth-token.py")
    
    print("\n" + "="*80)
    print("DIAGNOSTIC COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

