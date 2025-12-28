#!/usr/bin/env python3
"""
Ingest Enterprise Auth Strategy into Zep.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

# The content from enterprise_auth_strategy.md
STRATEGY_CONTENT = """
# Enterprise Authentication Strategy: From POC to Production

You asked how the current solution (disabling Platform Auth + App-level Bypass) correlates to a repeatable enterprise solution. This document outlines the architectural distinction and the path forward.

## Current State: POC / "Soft" Auth
Currently, we are using application-level logic to decide whether to enforce authentication.
- **Mechanism**: `auth.py` checks `AUTH_REQUIRED`. If false, it injects a "POC User" identity.
- **Requirement**: Azure Container Apps Platform Auth ("Easy Auth") must be **Disabled** (or set to Allow Anonymous) so that requests actually reach our `auth.py` logic.
- **Pros**: Rapid development, easy debugging, no external dependencies for local dev.
- **Cons**: Relies on code correctness for security; not suitable for Zero Trust environments.

## Target State: Enterprise / Zero Trust
In a production enterprise solution, we strictly separate **Authentication** (Who are you?) from **Authorization** (What can you do?).

### 1. Identity Gateway (Platform Auth)
Instead of disabling it, we will **Enable** Azure Container Apps Authentication.
- **Role**: Blocks unauthenticated traffic *before* it reaches the container.
- **Config**: Configured to require a valid Entra ID (Azure AD) token.
- **Benefit**: Zero Trust. If a request reaches your code, it is guaranteed to be from a valid identity. Your code never handles "public" traffic.

### 2. Application-Level RBAC
The application no longer "authenticates" users but "authorizes" them based on the token passed by the gateway.
- **Mechanism**: `auth.py` reads the `X-MS-CLIENT-PRINCIPAL` header injected by Azure.
- **Logic**: Maps the Entra ID claims (Groups/Roles) to Engram Roles (Admin, Analyst, etc.).

## The "Repeatable" Solution

To make this a repeatable artifact (Infrastructure-as-Code), the final bicep/terraform templates will:

1. **Enforce Platform Auth**: Set `azureContainerApps/authConfigs` to `enabled: true` with `unauthenticatedClientAction: Return401`.
2. **Configure Entra ID**: Automatically register the App Registration and pass Client ID/Secret to the container environment.
3. **Application Config**: Set `AUTH_REQUIRED=true`.

### Why the "Fix" felt like a workaround
The confusion arose because we had **Platform Auth enabled** (blocking requests) but **Application Auth disabled** (expecting to bypass). They contradicted each other.
- **Workaround (Now)**: Disable Platform Auth → Code handles everything (including bypass).
- **Enterprise (Future)**: Enable Platform Auth → Code handles Authorization only.

## Summary Checklist for Enterprise Transition
- [ ] Enable Azure Container Apps Authentication (Entra ID provider).
- [ ] Update `auth.py` to trust `X-MS-CLIENT-PRINCIPAL` headers (standard pattern for App Service/Container Apps).
- [ ] Set `AUTH_REQUIRED=true`.
- [ ] Remove `_no_auth_dependency` bypass logic from production builds.
"""

async def ingest_strategy():
    """Ingest the enterprise auth strategy as a memory session"""
    
    settings = get_settings()
    # AZURE ZEP URL
    zep_url = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
    
    # settings.zep_api_url = zep_url # This doesn't work on the object directly for client init often
    
    # We need to monkeypatch or pass it to client? 
    # ZepMemoryClient usually reads from settings singleton.
    # Let's override the env var for the process or just init client carefully.
    os.environ["ZEP_API_URL"] = zep_url
    
    # Re-get settings to ensure it picks up env var if pydantic reloads, 
    # or just trust the client will read os.environ if settings not frozen.
    # actually ZepMemoryClient uses settings.zep_api_url.
    
    # Better approach: Just set it on the settings object if it's mutable
    settings.zep_api_url = zep_url

    if not settings.zep_api_url:
        print("❌ ZEP_API_URL not configured. Cannot ingest memory.")
        return
    
    memory_client = ZepMemoryClient()
    
    # Use a unique but deterministic session ID for this concept
    session_id = "doc-enterprise-auth-strategy"
    user_id = "system"
    
    print(f"📝 Ingesting Enterprise Auth Strategy into Zep: {session_id}")
    print(f"   Zep URL: {settings.zep_api_url}")
    
    # 0. Ensure user exists
    try:
        user_payload = {
            "user_id": user_id,
            "metadata": {"role": "system", "name": "System"}
        }
        await memory_client._request("POST", "/api/v1/users", json=user_payload)
        print(f"✅ User confirmed/created: {user_id}")
    except Exception as e:
        print(f"ℹ️  User creation note (may already exist): {e}")

    # 1. Create/Update Session info
    try:
        session = await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "topic": "enterprise_authentication_strategy",
                "type": "architectural_decision_record",
                "participants": ["derek", "system"],
                "priority": "critical",
                "status": "approved",
                "created_by": "system",
                "content_type": "markdown_document",
                "summary": "Strategy for transition from POC auth (soft auth) to Enterprise Zero Trust (Gateway Auth)"
            }
        )
        print(f"✅ Session metadata updated: {session.get('session_id')}")
    except Exception as e:
        print(f"⚠️  Session update warning: {e}")

    # 2. Add the content as a "discussion" to provide context
    # converting the doc into a conversational format between User (question) and System (answer)
    messages = [
        {
            "role": "user",
            "content": "How does the current POC auth workaround correlated to a repeatable enterprise solution?"
        },
        {
            "role": "assistant",
            "content": f"Here is the detailed Enterprise Authentication Strategy outlining the transition from the current POC state to the target Zero Trust state:\n\n{STRATEGY_CONTENT}"
        },
        {
            "role": "system",
            "content": "The strategy was approved by the user on 2025-12-28. The current implementation (disabling platform auth) is confirmed as the correct interim step for the POC."
        }
    ]
    
    try:
        await memory_client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": "enterprise_auth_strategy.md"
            }
        )
        print(f"✅ Added {len(messages)} messages to memory")
    except Exception as e:
        print(f"❌ Failed to add messages: {e}")
        
    print(f"\n✅ Ingestion Complete. Memory available at session: {session_id}")

if __name__ == "__main__":
    asyncio.run(ingest_strategy())
