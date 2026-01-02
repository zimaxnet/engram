#!/usr/bin/env python3
"""
Test searching Zep memory for the GPT-5.1-chat API parameters fix episode.
"""

import asyncio
import os
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings

ZEP_URL = os.getenv("ZEP_API_URL", "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io")

# Set ZEP_API_URL if provided
if ZEP_URL:
    os.environ["ZEP_API_URL"] = ZEP_URL


async def search_episode():
    """Search for the GPT-5.1-chat API parameters fix episode."""
    print("=" * 80)
    print("Searching Zep Memory for GPT-5.1-chat API Parameters Fix Episode")
    print("=" * 80)
    print(f"ZEP URL: {ZEP_URL}")
    print()
    
    client = ZepMemoryClient()
    
    # Test queries
    queries = [
        "gpt-5.1-chat API parameters max_completion_tokens",
        "chat endpoint failing LLM API error",
        "temperature parameter not supported gpt-5.1-chat",
        "max_tokens vs max_completion_tokens",
    ]
    
    for query in queries:
        print(f"🔍 Search Query: {query}")
        print("-" * 80)
        
        try:
            results = await client.search_memory(
                query=query,
                limit=3
            )
            
            if results and len(results) > 0:
                print(f"✅ Found {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    print(f"\n  Result {i}:")
                    print(f"    Session ID: {result.get('session_id', 'N/A')}")
                    print(f"    Score: {result.get('score', 'N/A')}")
                    content = result.get('message', {}).get('content', '')
                    if content:
                        preview = content[:200].replace('\n', ' ')
                        print(f"    Preview: {preview}...")
            else:
                print("   ⚠️  No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Also try to get the specific session
    print("=" * 80)
    print("Getting Specific Session")
    print("=" * 80)
    session_id = "capability-gpt-5.1-chat-api-parameters-fix-2025-12-31"
    print(f"Session ID: {session_id}")
    
    try:
        session = await client._request("GET", f"/api/v1/sessions/{session_id}")
        if session:
            print(f"✅ Session found")
            print(f"   User ID: {session.get('user_id', 'N/A')}")
            print(f"   Metadata: {session.get('metadata', {})}")
            print(f"   Created: {session.get('created_at', 'N/A')}")
            
            # Get messages from this session
            messages = await client._request("GET", f"/api/v1/sessions/{session_id}/memory")
            if messages:
                print(f"   Messages: {len(messages.get('messages', []))}")
        else:
            print("   ⚠️  Session not found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(search_episode())

