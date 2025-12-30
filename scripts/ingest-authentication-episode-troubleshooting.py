#!/usr/bin/env python3
"""
Ingest Authentication & Episode Troubleshooting Workflow into Zep Memory

This episode documents the enterprise authentication flow setup and episode display fixes
for the dev/test environment.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path to import backend modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings


async def ingest_troubleshooting_episode():
    """Ingest the authentication and episode troubleshooting workflow into Zep"""
    
    session_id = "troubleshooting-auth-episodes-2025-12-30"
    user_id = "system-troubleshooting"
    
    summary = """Enterprise Authentication Flow Setup and Episode Display Troubleshooting

Resolved critical authentication and episode display issues in dev/test environment:
1. Fixed enterprise authentication flow (AUTH_REQUIRED=true enforcement)
2. Resolved episodes showing 'Unknown' agent and missing summaries
3. Fixed Continue Chat button not loading conversation history
4. Established proper token scope and audience validation for Entra External ID"""
    
    topics = [
        "authentication",
        "enterprise-auth",
        "entra-external-id",
        "episodes",
        "troubleshooting",
        "token-validation",
        "ciam",
        "dev-test-environment"
    ]
    
    messages = [
        {
            "role": "user",
            "content": """We're having 401 authentication errors and episodes are not loading. 
All episodes show 'Unknown' for agent_id, no summaries, and the Continue Chat button doesn't load the thread into chat."""
        },
        {
            "role": "assistant",
            "content": """I've identified multiple issues:

**Authentication Issues:**
1. Frontend was requesting basic scopes (openid, profile, email) instead of API scope
2. Backend was only validating client ID audience, not the api://{CLIENT_ID} format
3. Token scope mismatch between frontend request and backend validation

**Episode Display Issues:**
1. persist_conversation() wasn't setting session metadata (agent_id, summary, turn_count)
2. ChatPanel wasn't loading existing conversation history when sessionId provided
3. Episodes endpoint returning data but missing metadata fields

**Configuration:**
- AUTH_REQUIRED=true (enforced, no bypass)
- AZURE_AD_EXTERNAL_ID=true (Entra External ID / CIAM)
- AZURE_AD_EXTERNAL_DOMAIN=engramai
- AZURE_AD_CLIENT_ID=94d50189-d4de-4b80-8804-2f3bf2e2d14f"""
        },
        {
            "role": "user",
            "content": "Bypassing authentication is no longer acceptable. We need to work out the enterprise authentication flow. This is no longer a staging environment. This is now dev test."
        },
        {
            "role": "assistant",
            "content": """Understood. Let's establish proper enterprise authentication flow.

**Frontend Fixes (frontend/src/auth/authConfig.ts):**
1. Updated apiRequest to use correct scope: `api://${CLIENT_ID}/user_impersonation`
   - Matches the oauth2PermissionScopes defined in Entra app registration
   - Previous: Used `.default` scope which may not match backend expectations
   
2. Updated getAccessToken() to use apiRequest when CLIENT_ID is set
   - Ensures API tokens are requested with correct scope
   - Falls back to loginRequest only if CLIENT_ID not configured

**Backend Fixes (backend/api/middleware/auth.py):**
1. Enhanced audience validation to accept both formats:
   - Client ID itself (for .default scope tokens)
   - api://{CLIENT_ID} format (for user_impersonation scope tokens)
   
2. Token validation now:
   - Decodes token first to check actual audience
   - Validates against token's actual audience if it matches expected formats
   - Provides clear error messages for audience mismatches

**Episode Fixes (backend/memory/client.py):**
1. Updated persist_conversation() to set session metadata:
   - agent_id: From most recent assistant turn
   - summary: From context.episodic.summary or generated from recent turns
   - turn_count: From context.episodic.total_turns
   
2. Ensures sessions are created/updated with proper metadata via get_or_create_session()

**ChatPanel Fixes (frontend/src/components/ChatPanel/ChatPanel.tsx):**
1. Added logic to load existing messages when sessionIdProp is provided
2. Uses getEpisode() API to fetch transcript
3. Converts transcript to Message format and displays
4. Tracks loaded sessions to avoid reloading"""
        },
        {
            "role": "user",
            "content": "Commit push deployments are taking like a half an hour or so we have to wait"
        },
        {
            "role": "assistant",
            "content": """Committed and pushed all fixes in single commit:
- Commit: 5232862dc
- Title: "fix: Enterprise authentication flow and episode display issues"

**Key Configuration Verified:**
- AUTH_REQUIRED=true (enforced)
- AZURE_AD_EXTERNAL_ID=true
- AZURE_AD_EXTERNAL_DOMAIN=engramai
- AZURE_AD_CLIENT_ID=94d50189-d4de-4b80-8804-2f3bf2e2d14f
- Managed Identity: 47b574dc-9a18-45c0-9dd0-663999618c4f

**Deployment:**
- Takes ~30 minutes for full deployment
- Both frontend and backend changes included
- No auth bypass - proper enterprise flow established"""
        }
    ]
    
    # Format messages for Zep
    formatted_messages = [
        {
            "role": msg["role"],
            "content": msg["content"],
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "troubleshooting_workflow"
            }
        }
        for msg in messages
    ]
    
    print(f"📝 Ingesting troubleshooting episode into Zep...")
    print(f"   Session ID: {session_id}")
    print(f"   Summary: {summary[:100]}...")
    print(f"   Topics: {', '.join(topics)}")
    print(f"   Messages: {len(messages)}")
    print()
    
    try:
        # Get Zep URL from settings (uses ZEP_API_URL env var)
        settings = get_settings()
        if not settings.zep_api_url:
            print("❌ ZEP_API_URL not set. Please set it in environment or .env file")
            print("   Example: export ZEP_API_URL=http://zep-app.internal:8000")
            return False
        
        print(f"   Using Zep URL: {settings.zep_api_url}")
        client = ZepMemoryClient()
        
        # Create or update session with metadata
        await client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "summary": summary,
                "topics": topics,
                "agent_id": "system",
                "turn_count": len(messages),
                "source": "troubleshooting_ingestion",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        print(f"✅ Session created/updated: {session_id}")
        
        # Add messages to session
        await client.add_memory(
            session_id=session_id,
            messages=formatted_messages,
        )
        
        print(f"✅ Added {len(messages)} messages to session")
        print()
        print(f"🎉 Troubleshooting episode ingested successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   Agents can now reference this when troubleshooting:")
        print(f"   - Enterprise authentication setup")
        print(f"   - Episode display issues")
        print(f"   - Token scope and audience validation")
        print(f"   - Entra External ID (CIAM) configuration")
        
    except Exception as e:
        print(f"❌ Failed to ingest episode: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(ingest_troubleshooting_episode())

