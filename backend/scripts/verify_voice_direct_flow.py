#!/usr/bin/env python3
"""
Verify Voice Direct Flow Script

This script verifies the backend components of the Voice Live Direct architecture:
1. Fetches an ephemeral token from /voice/realtime/token.
2. Simulates a completed conversation turn by posting to /conversation/turn.
3. Checks Zep to confirm the turn was persisted.
"""

import asyncio
import os
import sys
import httpx
import uuid
import logging

# Add project root
sys.path.append(".")

# Configuration
API_BASE = "https://api.engram.work/api/v1"
TOKEN = os.getenv("AUTH_TOKEN")
AGENT_ID = "elena"

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def verify_flow():
    if not TOKEN:
        logger.error("Error: AUTH_TOKEN environment variable not set.")
        return

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    session_id = f"verify-{uuid.uuid4()}"
    logger.info(f"--- Starting Verification for Session: {session_id} ---")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Fetch Token
        logger.info("\n1. Requesting Voice Token...")
        try:
            resp = await client.post(
                f"{API_BASE}/voice/realtime/token",
                headers=headers,
                json={"agent_id": AGENT_ID, "session_id": session_id}
            )
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"   [SUCCESS] Received Token: {data.get('token')[:10]}...")
                logger.info(f"   [SUCCESS] Endpoint: {data.get('endpoint')}")
            else:
                logger.error(f"   [FAIL] Status {resp.status_code}: {resp.text}")
                return
        except Exception as e:
            logger.error(f"   [FAIL] Exception: {e}")
            return

        # 2. Persist Turn (Simulate Frontend)
        logger.info("\n2. Simulating Conversation Turn...")
        test_content = f"Verification Test Message {uuid.uuid4()}"
        turn_payload = {
            "session_id": session_id,
            "agent_id": AGENT_ID,
            "role": "user",
            "content": test_content
        }
        
        try:
            resp = await client.post(
                f"{API_BASE}/voice/conversation/turn",
                headers=headers,
                json=turn_payload
            )
            if resp.status_code == 200:
                logger.info("   [SUCCESS] Turn accepted by backend.")
            else:
                logger.error(f"   [FAIL] Status {resp.status_code}: {resp.text}")
                return
        except Exception as e:
            logger.error(f"   [FAIL] Exception: {e}")
            return

        # 3. Verify Ingestion (Check Episodes)
        logger.info("\n3. Verifying Persistence (checking episode details)...")
        # Give a moment for async background tasks
        await asyncio.sleep(2)
        
        try:
            # We need to fetch the specific episode. Since we don't have an endpoint to get by session_id directly publicly exposed
            # (unless it's mapped to ID), we'll list recent episodes and look for our session ID.
            resp = await client.get(
                f"{API_BASE}/memory/episodes",
                headers=headers,
                params={"limit": 10}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                episodes = data.get("episodes", [])
                found = False
                for ep in episodes:
                    # Depending on how session_id maps to ID, or if session_id is in summary/metadata
                    # In backend implementation: voice_context.episodic.conversation_id = turn.session_id
                    # So the episode ID might be the session_id or mapped to it.
                    if ep.get("id") == session_id:
                        found = True
                        logger.info(f"   [SUCCESS] Found episode: {ep.get('id')}")
                        logger.info(f"             Turn Count: {ep.get('turn_count')}")
                        # Ideally we'd check the transcript content too, but list might not have it.
                        break
                
                if not found:
                     logger.warning(f"   [WARN] Session ID {session_id} not found in recent episodes list.")
                     logger.info("          (This might be due to async ingestion delay or listing filtering)")
            else:
                logger.error(f"   [FAIL] Failed to list episodes: {resp.status_code}")

        except Exception as e:
             logger.error(f"   [FAIL] Exception verify ingestion: {e}")

    logger.info("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_flow())
