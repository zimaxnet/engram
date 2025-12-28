#!/usr/bin/env python3
"""
Register Agents as Users in Azure Zep.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

# Azure Zep URL
AZURE_ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"

AGENTS = [
    {
        "user_id": "elena",
        "metadata": {"name": "Elena", "role": "Business Analyst Agent", "type": "agent"}
    },
    {
        "user_id": "marcus",
        "metadata": {"name": "Marcus", "role": "Engineering Lead Agent", "type": "agent"}
    },
    {
        "user_id": "sage",
        "metadata": {"name": "Sage", "role": "Creative Director Agent", "type": "agent"}
    }
]

async def register_agents():
    settings = get_settings()
    settings.zep_api_url = AZURE_ZEP_URL
    
    memory_client = ZepMemoryClient()
    print(f"🚀 Connecting to Azure Zep: {AZURE_ZEP_URL}")

    for agent in AGENTS:
        user_id = agent["user_id"]
        try:
            print(f"Checking agent: {user_id}...")
            # Try create (idempotent-ish if we handle error, or we can check first)
            # Zep POST /users fails if exists usually, so let's try GET first
            existing = await memory_client._request("GET", f"/api/v1/users/{user_id}")
            if existing:
                print(f"✅ Agent exists: {user_id}")
            else:
                # This branch technically shouldn't hit if GET returns None, but logic depends on _request impl
                raise Exception("User not found (logic flow)")

        except Exception:
            # Likely 404, so create
            try:
                print(f"Creating agent: {user_id}...")
                await memory_client._request("POST", "/api/v1/users", json=agent)
                print(f"✅ Created agent: {user_id}")
            except Exception as e:
                print(f"❌ Failed to create agent {user_id}: {e}")

if __name__ == "__main__":
    asyncio.run(register_agents())
