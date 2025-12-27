#!/usr/bin/env python3
"""
List All Sessions Script

Fetches and displays all sessions currently stored in Zep memory.
Useful for verifying data ingestion and debugging retrieval issues.
"""

import asyncio
import logging
import sys
import json
from datetime import datetime

# Add the project root to the python path
sys.path.append(".")

import asyncio
import logging
import sys
import httpx
from datetime import datetime

# Add the project root to the python path
sys.path.append(".")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

import os

# Constants
API_URL = "https://api.engram.work/api/v1/memory/episodes"
TOKEN = os.getenv("AUTH_TOKEN", "REPLACE_WITH_YOUR_TOKEN")

async def list_all_sessions():
    print(f"\n{'='*80}")
    print(f"AZURE ENGRAM MEMORY SESSION LISTING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    try:
        print(f"Connecting to: {API_URL}...\n")

        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(API_URL, headers=headers, params={"limit": 50})
            
            if response.status_code != 200:
                print(f"Error fetching sessions: {response.status_code}")
                print(response.text)
                return

            data = response.json()
            episodes = data.get("episodes", [])
            total_count = data.get("total_count", 0)

            print(f"Found {len(episodes)} episodes (Total: {total_count}):\n")
            print(f"{'Session ID':<35} | {'Agent':<15} | {'Turns':<5} | {'Summary'}")
            print(f"{'-'*35}-+-{'-'*15}-+-{'-'*5}-+-{'-'*40}")

            for ep in episodes:
                ep_id = ep.get("id", "N/A")
                agent = ep.get("agent_id", "unknown")
                turns = ep.get("turn_count", 0)
                summary = ep.get("summary", "No summary available")
                
                # Truncate summary for display
                if len(summary) > 37:
                    summary = summary[:37] + "..."
                    
                print(f"{ep_id:<35} | {agent:<15} | {turns:<5} | {summary}")

            print(f"\n{'='*80}\n")

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(list_all_sessions())
