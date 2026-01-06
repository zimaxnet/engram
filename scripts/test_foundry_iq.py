#!/usr/bin/env python3
"""
Test Foundry IQ Client

Tests the Foundry IQ client for enterprise document search.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.agents.foundry_iq_client import get_foundry_iq_client
from backend.core import get_settings

async def main():
    """Test Foundry IQ client."""
    settings = get_settings()
    
    print("=" * 60)
    print("Foundry IQ Client Test")
    print("=" * 60)
    print()
    
    # Check configuration
    print("Configuration:")
    print(f"  USE_FOUNDRY_IQ: {settings.use_foundry_iq}")
    print(f"  FOUNDRY_IQ_KB_ID: {settings.foundry_iq_knowledge_base_id}")
    print(f"  AZURE_FOUNDRY_AGENT_ENDPOINT: {settings.azure_foundry_agent_endpoint}")
    print(f"  AZURE_FOUNDRY_AGENT_PROJECT: {settings.azure_foundry_agent_project}")
    print()
    
    if not settings.use_foundry_iq:
        print("❌ Foundry IQ is not enabled. Set USE_FOUNDRY_IQ=true")
        return
    
    if not settings.foundry_iq_knowledge_base_id:
        print("❌ Knowledge base ID not configured. Set FOUNDRY_IQ_KB_ID")
        return
    
    # Get client
    client = get_foundry_iq_client()
    if not client:
        print("❌ Failed to initialize Foundry IQ client")
        return
    
    print("✅ Foundry IQ client initialized")
    print()
    
    # Test 1: List knowledge bases
    print("Test 1: List Knowledge Bases")
    print("-" * 60)
    try:
        knowledge_bases = await client.list_knowledge_bases()
        print(f"✅ Found {len(knowledge_bases)} knowledge bases")
        for kb in knowledge_bases[:5]:  # Show first 5
            print(f"  - {kb.get('name', 'Unknown')} (ID: {kb.get('id', 'Unknown')})")
    except Exception as e:
        print(f"❌ Failed to list knowledge bases: {e}")
    print()
    
    # Test 2: Get knowledge base info
    print("Test 2: Get Knowledge Base Info")
    print("-" * 60)
    try:
        kb_info = await client.get_knowledge_base()
        print(f"✅ Knowledge base retrieved:")
        print(f"  Name: {kb_info.get('name', 'Unknown')}")
        print(f"  ID: {kb_info.get('id', 'Unknown')}")
        print(f"  Status: {kb_info.get('status', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to get knowledge base: {e}")
    print()
    
    # Test 3: Search
    print("Test 3: Search Knowledge Base")
    print("-" * 60)
    test_queries = [
        "authentication",
        "project management",
        "architecture",
    ]
    
    for query in test_queries:
        try:
            results = await client.search(query=query, limit=5)
            print(f"✅ Query: '{query}'")
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results[:3], 1):  # Show top 3
                content = result.get("content", "")[:100]
                score = result.get("score", 0.0)
                source = result.get("source", "unknown")
                print(f"   {i}. [{source}] (score: {score:.3f}) {content}...")
        except Exception as e:
            print(f"❌ Query '{query}' failed: {e}")
        print()
    
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

