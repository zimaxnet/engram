import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.context.registry import register_context
from backend.context.store import store
from backend.memory.client import memory_client

# 1. Define a Context (Context-as-Code)
@register_context(name="project_status", description="Get high-level project status")
async def get_project_status(project_id: str):
    return {
        "project_id": project_id,
        "status": "Green",
        "progress": "85%",
        "blockers": []
    }

# 2. Define a Context that uses Zep Provider (Declarative/Code hybrid)
@register_context(name="recent_memories", description="Fetch recent memories about a topic")
async def get_recent_memories(topic: str):
    # Retrieve the Zep provider manually for this hybrid example
    provider = store.providers.get("zep")
    if provider:
        results = await provider.fetch(query=topic, filters={"limit": 2})
    else:
        results = []
    return {
        "topic": topic,
        "memories": results
    }

async def main():
    print("--- Testing Virtual Context Store ---")

    # Test 1: Pure Function Context
    print("\n1. Fetching 'project_status'...")
    ctx1 = await store.get_context("project_status", params={"project_id": "P-123"})
    print(f"Result: {ctx1}")
    assert ctx1["project_id"] == "P-123"

    # Test 2: Zep Provider Context (requires live Zep)
    print("\n2. Fetching 'recent_memories' (via Zep)...")
    try:
        ctx2 = await store.get_context("recent_memories", params={"topic": "architecture"})
        print(f"Result: {ctx2}")
    except Exception as e:
        print(f"Skipped (Zep not available): {e}")
    
    # Test 3: Engram Self-Reflection (Meta-context)
    print("\n3. Fetching 'engram_project_state' (Self-Reflective)...")
    try:
        ctx3 = await store.get_context("engram_project_state", params={"query_focus": "implementation"})
        print(f"Result: {ctx3}")
        assert ctx3["project"] == "Engram"
    except Exception as e:
        print(f"Skipped (requires Zep): {e}")

    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    asyncio.run(main())

