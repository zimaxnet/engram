#!/usr/bin/env python3
"""
Ingest Zep Connectivity Finding into Zep.
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

async def ingest_finding():
    """Ingest the Zep connectivity finding as a memory session"""
    
    settings = get_settings()
    
    # Check if URL is set (allow override via env var for script run)
    zep_url = os.environ.get("ZEP_API_URL", settings.zep_api_url)
    
    if not zep_url:
        print("❌ ZEP_API_URL not configured. Cannot ingest memory.")
        return
    
    # Temporarily patch settings for this run instance if needed
    if zep_url != settings.zep_api_url:
        settings.zep_api_url = zep_url

    memory_client = ZepMemoryClient()
    
    session_id = "sess-zep-connectivity-troubleshooting"
    user_id = "system"
    
    print(f"📝 Ingesting Zep Connectivity Finding: {session_id}")
    print(f"   Zep URL: {zep_url}")
    
    # 0. Ensure user exists
    try:
        user_payload = {
            "user_id": user_id,
            "metadata": {"role": "system", "name": "System"}
        }
        await memory_client._request("POST", "/api/v1/users", json=user_payload)
        print(f"✅ User confirmed/created: {user_id}")
    except Exception as e:
        print(f"ℹ️  User creation note: {e}")

    # 1. Create/Update Session info
    try:
        session = await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "topic": "zep_connectivity_latency",
                "type": "post_mortem",
                "participants": ["derek", "system"],
                "priority": "high",
                "status": "resolved",
                "created_by": "system",
                "summary": "Resolved 30s latency in Episodes by switching from internal to external Zep URL."
            }
        )
        print(f"✅ Session metadata updated: {session.get('session_id')}")
    except Exception as e:
        print(f"⚠️  Session update warning: {e}")

    # 2. Add the conversation content
    messages = [
        {
            "role": "user",
            "content": "Report on the 'spinning episodes' incident. What was the root cause of the 30-second latency?"
        },
        {
            "role": "assistant",
            "content": """**Incident Report: Slow Episodes / Zep Connectivity**

**Symptom**: 
The `/episodes` endpoint was taking ~30.2 seconds to respond, causing the UI to "spin" indefinitely for users. Logs showed a successful 200 OK response but with an empty list, hiding the underlying error.

**Investigation**:
Backend logs revealed that `timeout` errors were occurring in `backend.memory.client` when attempting to connect to Zep.
The configuration was set to use the internal container URL:
`http://staging-env-zep...:8000`

**Root Cause**:
The internal port 8000 connectivity between the API container and Zep container in Azure Container Apps was unreliable or blocked, causing the `httpx` client to wait for the full default timeout (30s) before failing.

**Resolution**:
We switched the `ZEP_API_URL` environment variable to use the **External FQDN** with HTTPS (Port 443):
`https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io`

**Result**:
- Latency dropped from ~30s to <1s (0.45s measured).
- Episodes now load instantly.

**Side Note**: 
During the fix, the `az containerapp update` command inadvertently reset the Platform Authentication settings, temporarily causing 401 errors. This was resolved by re-disabling Platform Auth to restore the "Easy Auth" bypass."""
        },
        {
            "role": "system",
            "content": "This finding is critical for future deployments: Prefer external HTTPS FQDNs for service-to-service communication in this environment unless internal ingress is explicitly verified."
        }
    ]
    
    try:
        await memory_client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": "manual_ingestion"
            }
        )
        print(f"✅ Added {len(messages)} messages to memory")
    except Exception as e:
        print(f"❌ Failed to add messages: {e}")
        
    print(f"\n✅ Ingestion Complete. Memory available at session: {session_id}")

if __name__ == "__main__":
    asyncio.run(ingest_finding())
