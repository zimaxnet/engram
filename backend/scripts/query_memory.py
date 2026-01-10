#!/usr/bin/env python3
"""
Query CtxGraph Script (Antigravity Interface)

This script provides a CLI interface for AI Agents (Antigravity, Cursor, VSCode)
to query the CtxGraph (Zep temporal knowledge graph) across any environment.

It exposes:
1. Hybrid Search (Keyword + Semantic) via OpenContextGraph API
2. Knowledge Graph Facts
3. Recent Episodes

Usage:
    # Query local CtxGraph (default)
    python -m backend.scripts.query_memory --query "voice live config"
    
    # Query Azure production CtxGraph
    python -m backend.scripts.query_memory --env azure --query "voice live config"
    
    # List Azure episodes
    python -m backend.scripts.query_memory --env azure --episodes --limit 5
    
    # Get facts from Azure
    python -m backend.scripts.query_memory --env azure --facts --user-id "user-derek"

Environments:
    local   - http://localhost:8000 (default)
    azure   - https://zep.engram.work (production)
    staging - https://zep-staging.engram.work (if available)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure concise logging for CLI output
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("query_memory")

from backend.memory.environments import ENVIRONMENT_PRESETS


def apply_environment(env_name: str) -> str:
    """Apply environment preset and return the Zep URL."""
    if env_name not in ENVIRONMENT_PRESETS:
        print(f"❌ Unknown environment: {env_name}")
        print(f"   Available: {', '.join(ENVIRONMENT_PRESETS.keys())}")
        sys.exit(1)
    
    preset = ENVIRONMENT_PRESETS[env_name]
    zep_url = preset["ZEP_API_URL"]
    
    # Override the environment variable for this process
    os.environ["ZEP_API_URL"] = zep_url
    
    return zep_url


async def query_memory(
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    mode: str = "hybrid",
    limit: int = 5,
    env_name: str = "local"
):
    # Apply environment preset BEFORE importing settings
    zep_url = apply_environment(env_name)
    
    # Import after environment is set
    from backend.memory.client import ZepMemoryClient
    
    # Create client with explicit URL override
    client = ZepMemoryClient()
    # Force the URL from our preset (in case settings cached old value)
    client.zep_url = zep_url
    
    env_info = ENVIRONMENT_PRESETS[env_name]
    print(f"🧠 Engram Memory Query")
    print(f"   Environment: {env_name.upper()} ({env_info['description']})")
    print(f"   URL: {zep_url}")
    print(f"   Mode: {mode}")
    print(f"   User: {user_id or 'All Users'}")
    print("-" * 60)

    if mode == "hybrid":
        if not query:
            print("❌ Error: --query is required for hybrid search")
            return

        # For hybrid search, we don't need to create a user/session
        # The search_memory function lists all sessions and searches across them
        results = await client.search_memory(
            session_id="global-search",  # Not actually used for session-based search
            query=query,
            limit=limit,
            user_id=user_id  # Optional filter
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


def list_environments():
    """Print available environments."""
    print("🌍 Available Environments:\n")
    for name, config in ENVIRONMENT_PRESETS.items():
        print(f"  {name:10} → {config['ZEP_API_URL']}")
        print(f"             {config['description']}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Query CtxGraph (Engram Memory Graph) - Local, Azure, K8s",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query Azure production for VoiceLive info
  python -m backend.scripts.query_memory --env azure -q "voice live config"
  
  # List recent episodes from Azure
  python -m backend.scripts.query_memory --env azure --episodes
  
  # Get facts for a user from Azure
  python -m backend.scripts.query_memory --env azure --facts -u "user-derek"
  
  # List available environments
  python -m backend.scripts.query_memory --list-envs
"""
    )
    parser.add_argument("-e", "--env", default="local", 
                        help="Environment: local, azure, staging (default: local)")
    parser.add_argument("-q", "--query", help="Search query text")
    parser.add_argument("-u", "--user-id", help="Filter by User ID")
    parser.add_argument("-l", "--limit", type=int, default=5, help="Max results")
    parser.add_argument("--facts", action="store_true", help="Mode: Get Knowledge Graph Facts")
    parser.add_argument("--episodes", action="store_true", help="Mode: List Episodes")
    parser.add_argument("--list-envs", action="store_true", help="List available environments")
    
    args = parser.parse_args()
    
    if args.list_envs:
        list_environments()
        return
    
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
            limit=args.limit,
            env_name=args.env
        ))
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
