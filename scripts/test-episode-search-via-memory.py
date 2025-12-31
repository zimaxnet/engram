#!/usr/bin/env python3
"""
Test searching for the GPT-5.1-chat API parameters fix episode via memory client.
This simulates what agents do when searching memory.
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


async def search_for_episode():
    """Search for the GPT-5.1-chat API parameters fix episode using memory client."""
    print("=" * 80)
    print("Searching Memory for GPT-5.1-chat API Parameters Fix Episode")
    print("=" * 80)
    print(f"ZEP URL: {ZEP_URL}")
    print()
    
    client = ZepMemoryClient()
    
    # Test queries that should find the episode
    test_queries = [
        "chat endpoint failing LLM API error",
        "gpt-5.1-chat API parameters max_completion_tokens",
        "temperature parameter not supported gpt-5.1-chat",
        "max_tokens vs max_completion_tokens troubleshooting",
        "chat error messages tokens_used 0",
    ]
    
    print("Testing memory search queries that should find the episode:\n")
    
    for query in test_queries:
        print(f"🔍 Query: \"{query}\"")
        print("-" * 80)
        
        try:
            # Use "global-search" session_id like agents do in _reason_node()
            results = await client.search_memory(
                session_id="global-search",  # This searches across all sessions
                query=query,
                limit=5
            )
            
            if results and len(results) > 0:
                print(f"✅ Found {len(results)} results")
                for i, result in enumerate(results[:3], 1):
                    session_id = result.get("session_id", "unknown")
                    score = result.get("score", 0)
                    content = result.get("content", "")
                    metadata = result.get("metadata", {})
                    
                    print(f"\n  Result {i}:")
                    print(f"    Session ID: {session_id}")
                    print(f"    Score: {score:.3f}")
                    
                    # Check if this is our episode
                    if "gpt-5.1-chat-api-parameters-fix" in session_id:
                        print(f"    🎯 THIS IS OUR EPISODE!")
                    
                    # Show metadata if available
                    if metadata:
                        title = metadata.get("title", "")
                        if title:
                            print(f"    Title: {title}")
                    
                    # Show content preview
                    if content:
                        preview = content[:200].replace('\n', ' ')
                        print(f"    Preview: {preview}...")
            else:
                print("   ⚠️  No results found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print("If the episode appears in any of the search results above,")
    print("it means agents CAN access this information when users report")
    print("chat or voice failures. The episode will be automatically")
    print("injected into the agent's context during conversations.")
    print()


if __name__ == "__main__":
    asyncio.run(search_for_episode())

