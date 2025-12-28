#!/usr/bin/env python3
"""
Ingest Entra External ID Authentication Episode.

Documents the complete CIAM setup with Google social login.
"""

import asyncio
import os
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
SESSION_ID = "capability-entra-external-id"
USER_ID = "system"

EPISODE_CONTENT = """
# Capability: Entra External ID Authentication (Dec 28, 2025)

## Summary
Implemented Microsoft Entra External ID (CIAM) for user authentication with Google social login. This solves the recurring 401 authentication issue after deployments and provides a proper identity platform.

## Problem Solved
- Platform Auth was re-enabled on every Azure Container Apps deployment
- Required manual `az containerapp auth update --enabled false` after each deploy
- No proper user authentication mechanism

## Solution: Entra External ID

### Tenant Configuration
- **Tenant**: engramai.onmicrosoft.com
- **Authority**: https://engramai.ciamlogin.com/engramai.onmicrosoft.com
- **App Registration**: engram-frontend
- **Client ID**: 94d50189-d4de-4b80-8804-2f3bf2e2d14f

### Identity Providers
- Google OAuth 2.0 (social login)

### User Flow
- SignUpSignIn with Google provider
- Collects: Email, Display Name

## Implementation

### Frontend (MSAL.js)
- `frontend/src/auth/authConfig.ts` - MSAL configuration for ciamlogin.com
- `frontend/src/auth/AuthContext.tsx` - React context with login/logout/getToken
- `frontend/src/main.tsx` - MsalProvider wrapper

### Backend (JWT Validation)
- `backend/api/middleware/auth.py` - Updated for External ID endpoints
  - Detects AZURE_AD_EXTERNAL_ID=true
  - Uses ciamlogin.com for JWKS and issuer validation
  - Compatible with both workforce and external identities

### Infrastructure
- `infra/main.bicep` - External ID parameters
- `infra/modules/backend-aca.bicep` - Environment variables
- `.github/workflows/deploy.yml` - Secrets passed to build

## Secrets Configured

### GitHub Actions
- AZURE_AD_TENANT_ID: engramai.onmicrosoft.com
- AZURE_AD_CLIENT_ID: 94d50189-d4de-4b80-8804-2f3bf2e2d14f
- AZURE_AD_EXTERNAL_ID: true
- AZURE_AD_EXTERNAL_DOMAIN: engramai

### Azure Key Vault
- azure-ad-client-id
- azure-ad-tenant-id

## Authentication Flow
1. User clicks "Sign in with Google" on frontend
2. MSAL redirects to engramai.ciamlogin.com
3. User authenticates with Google
4. Entra issues JWT (ID token + access token)
5. Frontend stores tokens, passes to backend in Authorization header
6. Backend validates JWT using ciamlogin.com JWKS
7. User identity available in API routes

## Google OAuth Setup
- Created OAuth 2.0 credentials in Google Cloud Console
- Redirect URI: https://engramai.ciamlogin.com/engramai.onmicrosoft.com/oauth2/authresp
- Added to Entra External ID identity providers

## Key Files Modified
1. `backend/api/middleware/auth.py` - External ID support
2. `frontend/src/auth/` - New auth module (authConfig.ts, AuthContext.tsx, index.ts)
3. `frontend/src/main.tsx` - MsalProvider wrapper
4. `frontend/.env.example` - Configuration template
5. `infra/main.bicep` - External ID parameters
6. `infra/modules/backend-aca.bicep` - Environment variables
7. `.github/workflows/deploy.yml` - Build and deploy integration
8. `docs/architecture/entra-external-id.md` - Documentation

## Next Steps
- Enable AUTH_REQUIRED=true for production
- Add role-based access control (RBAC)
- Configure token refresh handling
- Add logout button to UI
"""

METADATA = {
    "type": "capability",
    "date": "2025-12-28",
    "topics": ["authentication", "Entra External ID", "CIAM", "Google OAuth", "MSAL", "JWT"],
    "summary": "Entra External ID (CIAM) with Google social login for secure user authentication",
    "components": ["auth.py", "authConfig.ts", "AuthContext.tsx", "main.bicep"],
}


async def main():
    print("🚀 Ingesting Entra External ID Episode")
    print(f"Target: {ZEP_URL}")
    print(f"Session: {SESSION_ID}")
    print("-" * 50)
    
    settings = get_settings()
    settings.zep_api_url = ZEP_URL
    os.environ["ZEP_API_URL"] = ZEP_URL
    
    memory_client = ZepMemoryClient()
    
    # Create session
    try:
        await memory_client.get_or_create_session(SESSION_ID, USER_ID, METADATA)
        print(f"✅ Session: {SESSION_ID}")
    except Exception as e:
        print(f"ℹ️  Session note: {e}")
    
    # Add content
    await memory_client.add_memory(
        session_id=SESSION_ID,
        messages=[{"role": "system", "content": EPISODE_CONTENT}],
        metadata=METADATA
    )
    print(f"✅ Episode ingested ({len(EPISODE_CONTENT)} chars)")
    
    # Also add to vector store for semantic search
    try:
        from backend.memory.vector_store import store_with_embedding
        await store_with_embedding(
            session_id=SESSION_ID,
            content=EPISODE_CONTENT,
            title="Entra External ID Authentication Capability",
            topics=METADATA["topics"],
            source_type="capability",
        )
        print("✅ Embedding stored in vector_store")
    except Exception as e:
        print(f"⚠️  Vector store: {e}")
    
    print("-" * 50)
    print("✅ Memory enrichment complete!")


if __name__ == "__main__":
    asyncio.run(main())
