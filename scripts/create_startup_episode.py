#!/usr/bin/env python3
"""
Ingest the Startup Recovery Scenario as a Zep Episode.
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

async def ingest_episode():
    settings = get_settings()
    
    # Azure Zep URL
    AZURE_ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
    
    # Override settings for this script execution
    settings.zep_api_url = AZURE_ZEP_URL
    
    if not settings.zep_api_url:
        print("❌ ZEP_API_URL not configured.")
        return
    
    memory_client = ZepMemoryClient()
    session_id = f"sess-startup-recovery-{datetime.now().strftime('%Y%m%d')}"
    user_id = "derek"

    print(f"📝 Ingesting Startup Recovery Episode: {session_id}")

    # 0. Ensure User Exists
    try:
        user_payload = {
            "user_id": user_id,
            "metadata": {"name": "Derek", "role": "admin"}
        }
        await memory_client._request("POST", "/api/v1/users", json=user_payload)
        print(f"✅ User confirmed: {user_id}")
    except Exception as e:
        print(f"ℹ️  User note (may exist): {e}")

    # 1. Ensure Session Exists
    try:
        await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "topic": "system_recovery_troubleshooting",
                "type": "engineering_incident",
                "participants": ["derek", "system"],
                "status": "resolved",
                "summary": "Troubleshooting sequence for Azure startup: Docker failure, Platform Auth mismatch, Zep Ingress connectivity."
            }
        )
    except Exception as e:
        print(f"⚠️ Session creation note: {e}")

    # 2. Ingest Messages representing the timeline
    messages = [
        # --- Local Docker Issue ---
        {
            "role": "user",
            "content": "I took a break, turned off the database and all of the containers when turning them back on none of the systems come online."
        },
        {
            "role": "system",
            "content": "Diagnosis: Docker daemon was not running. Started Docker Desktop and ran `docker-compose up -d`. All local services (Postgres, Temporal, Zep, API) are now healthy."
        },
        # --- Azure Platform Auth Issue ---
        {
            "role": "user",
            "content": "I'm talking about in Azure. If I wake up in the morning, I need to be able to turn on the database and the containers and have it work."
        },
        {
            "role": "system",
            "content": "Diagnosis: Azure Platform Auth was Enabled, but application `AUTH_REQUIRED=false`. This caused a 401 Bypass Mismatch. \nAction: Disabled Azure Platform Auth on `staging-env-api`. \nResult: Public Health Endpoint returned 200 OK."
        },
        # --- Zep Connectivity Issue ---
        {
            "role": "user",
            "content": "Episodes are spinning. I think external port 8000 keeps getting reverted."
        },
        {
            "role": "system",
            "content": "Diagnosis: `staging-env-zep` had NO Ingress enabled, and API was trying to hit port 8000 externally (which requires 443 on Azure CA). \nAction: Enabled Ingress on `staging-env-zep` (Target 8000, External). Updated `ZEP_API_URL` on all services to the HTTPS FQDN. \nResult: Zep Health verified."
        },
        # --- Reliability Confirmation ---
        {
            "role": "user",
            "content": "Do I need to do this every morning?"
        },
        {
            "role": "system",
            "content": "No. The Auth fix and Zep Ingress fix are persistent infrastructure changes. The `/azure-startup` workflow has been optimized with a final health check. You are good to go."
        }
    ]

    try:
        await memory_client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={
                "source": "troubleshooting_script",
                "ingested_at": datetime.now(timezone.utc).isoformat()
            }
        )
        print(f"✅ Successfully ingested {len(messages)} messages.")
    except Exception as e:
        print(f"❌ Failed to ingest messages: {e}")
        
    print(f"\n✅ Incident recorded. Session ID: {session_id}")

if __name__ == "__main__":
    asyncio.run(ingest_episode())
