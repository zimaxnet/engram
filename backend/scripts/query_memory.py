#!/usr/bin/env python3
"""
Query Memory Script (Antigravity Interface)

This script provides a CLI interface for the Antigravity Agent to query Zep memory.
It exposes:
1. Hybrid Search (Keyword + Semantic)
2. Knowledge Graph Facts
3. Recent Episodes

Usage:
    python -m backend.scripts.query_memory --query "voice live config"
    python -m backend.scripts.query_memory --facts --user-id "user-derek"
    python -m backend.scripts.query_memory --episodes --limit 5
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Optional

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

# Configure concise logging for CLI output
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("query_memory")

async def query_memory(
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    mode: str = "hybrid",
    limit: int = 5
):
    client = ZepMemoryClient()
    
    print(f"🔍 Querying Zep Memory ({mode})...")
    print(f"   URL: {client.zep_url}")
    print(f"   User: {user_id or 'All Users'}")
    print("-" * 60)

    if mode == "hybrid":
        if not query:
            print("❌ Error: --query is required for hybrid search")
            return

        # Generic search session
        search_user_id = user_id or "system-search"
        session_id = f"search-{datetime.utcnow().strftime('%Y%m%d')}"
        
        # CRITICAL: Ensure user exists first
        await client.get_or_create_user(
            user_id=search_user_id,
            metadata={"display_name": "Antigravity Search System"}
        )

        # Ensure search session exists (minimal overhead)
        await client.get_or_create_session(session_id, search_user_id)

        results = await client.search_memory(
            session_id=session_id,
            query=query,
            limit=limit,
            user_id=user_id
        )

        if not results:
            print("No matching memories found.")
            return

        print(f"Found {len(results)} results:\n")
        for i, res in enumerate(results, 1):
            score = res.get("score", 0.0)
            content = res.get("content", "").strip()
            sid = res.get("session_id", "unknown")
            meta = res.get("metadata", {})
            source_type = res.get("source_type", "unknown")
            
            print(f"[{i}] Score: {score:.2f} | Session: {sid} | Type: {source_type}")
            print(f"    {content[:200]}..." if len(content) > 200 else f"    {content}")
            if meta:
                print(f"    Metadata: {json.dumps(meta, default=str)}")
            print("")

    elif mode == "facts":
        if not user_id:
            print("❌ Error: --user-id is required for fact retrieval")
            return

        facts = await client.get_facts(user_id=user_id, query=query, limit=limit)
        
        if not facts:
            print(f"No facts found for user {user_id}.")
            return

        print(f"Found {len(facts)} facts:\n")
        for i, fact in enumerate(facts, 1):
            print(f"[{i}] {fact.content}")
            if fact.metadata:
                print(f"    Meta: {fact.metadata}")
            print("")

    elif mode == "episodes":
        limit = min(limit, 20)
        sessions = await client.list_sessions(user_id=user_id, limit=limit)
        
        if not sessions:
            print("No episodes found.")
            return

        print(f"Found {len(sessions)} recent episodes:\n")
        for i, sess in enumerate(sessions, 1):
            sid = sess.get("session_id")
            created = sess.get("created_at")
            meta = sess.get("metadata", {})
            summary = meta.get("summary", "No summary")
            topics = meta.get("topics", [])
            
            print(f"[{i}] {sid} ({created})")
            print(f"    Summary: {summary}")
            if topics:
                print(f"    Topics: {', '.join(topics)}")
            print("")

def main():
    parser = argparse.ArgumentParser(description="Query Zep Memory")
    parser.add_argument("-q", "--query", help="Search query text")
    parser.add_argument("-u", "--user-id", help="Filter by User ID")
    parser.add_argument("-l", "--limit", type=int, default=5, help="Max results")
    parser.add_argument("--facts", action="store_true", help="Mode: Get Knowledge Graph Facts")
    parser.add_argument("--episodes", action="store_true", help="Mode: List Episodes")
    
    args = parser.parse_args()
    
    mode = "hybrid"
    if args.facts:
        mode = "facts"
    elif args.episodes:
        mode = "episodes"

    try:
        asyncio.run(query_memory(
            query=args.query,
            user_id=args.user_id,
            mode=mode,
            limit=args.limit
        ))
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
