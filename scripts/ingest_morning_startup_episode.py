#!/usr/bin/env python3
"""
Ingest Morning Startup Episode into Zep Memory

This script ingests the morning startup findings as an episode into Zep,
making the learnings searchable via keyword, vector, and graph queries.

Usage: python -m backend.scripts.ingest_startup_episode
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EPISODE_CONTENT = """
# Morning Startup Report: 2026-01-03

## Context
Following a breakthrough with recursive engineering yesterday, this morning's startup verified system availability and addressed expected CORS/Auth issues.

## Key Findings

### 1. Stale Container App Revision URL Fixed
- Problem: Hardcoded revision staging-env-api--0000095 was stale
- Solution: Use api.engram.work and dynamic revision lookup
- Current active revision: staging-env-api--0000131

### 2. Platform Auth Configuration
- Platform Auth correctly DISABLED with AllowAnonymous
- No CORS/Auth reversion issues today

### 3. Knowledge Graph Empty State
- Expected behavior for fresh session
- Entities populate as conversations are ingested by Zep

## Verification Results
- PostgreSQL: Ready
- Temporal Server: Running
- Zep Memory: Running
- API: Healthy
- Episodes: 100 displayed
- Chat: Elena responding
- Stories: Artifacts visible
- Voice: Connected
- Knowledge Graph: 0 entities (fresh state)

## Memory Recall Test
Elena successfully:
- Ingested keyword SUNRISE_VERIFICATION_20260103
- Recalled keyword on request
- Performed episodic memory search

## Artifacts Created
- verify-memory-e2e.sh: E2E memory pipeline verification
- azure-startup.md updated with step 10 for memory verification

## Key Learning
Antigravity has direct access to Engram Knowledge Graph via query_memory.py:
- Hybrid search: python -m backend.scripts.query_memory --query 'YOUR QUERY'
- Facts: python -m backend.scripts.query_memory --facts --user-id 'user-derek'
- Episodes: python -m backend.scripts.query_memory --episodes

Always query memory before asking for context that might already be documented.
"""

async def main():
    from backend.memory.client import ZepMemoryClient
    
    client = ZepMemoryClient()
    session_id = f"startup-episode-{datetime.utcnow().strftime('%Y%m%d')}"
    user_id = "system"
    
    logger.info(f"Ingesting morning startup episode: {session_id}")
    
    # Ensure user exists
    await client.get_or_create_user(
        user_id=user_id,
        metadata={"display_name": "System Episodes", "role": "system"}
    )
    
    # Create session with metadata
    await client.get_or_create_session(
        session_id=session_id,
        user_id=user_id,
        metadata={
            "title": "Morning Startup Report 2026-01-03",
            "summary": "Verification of Azure components, stale revision fix, Platform Auth status, UI navigation, and memory recall testing",
            "topics": ["startup", "azure", "cors", "auth", "memory", "verification", "recursive-engineering"],
            "episode_type": "operations",
            "date": datetime.utcnow().isoformat(),
        }
    )
    
    # Add the episode content
    await client.add_memory(
        session_id=session_id,
        messages=[
            {"role": "user", "content": "Document this morning's startup verification findings."},
            {"role": "assistant", "content": EPISODE_CONTENT},
        ],
        metadata={"enrichment_type": "startup_report"}
    )
    
    logger.info(f"✅ Episode ingested: {session_id}")
    logger.info("   Topics: startup, azure, cors, auth, memory, verification, recursive-engineering")
    logger.info("   This episode is now searchable via keyword, vector, and graph queries.")

if __name__ == "__main__":
    asyncio.run(main())
