import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.context.registry import register_context
from backend.context.store import store
from backend.memory.client import memory_client, MockZepClient

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
    provider = store.providers["zep"]
    results = await provider.fetch(query=topic, filters={"limit": 2})
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

    # --- Pre-load Mock Data for Test 2 & 3 ---
    if isinstance(memory_client.client, MockZepClient):
        # We need to manually inject the facts because this is a fresh process
        print("Injecting Mock Data for Verification...")
        if not hasattr(memory_client.client.graph, "facts"):
             memory_client.client.graph.facts = []
        
        memory_client.client.graph.facts.append(
             {"fact": "Engram Virtual Context Store implementation plan", "uuid": "mock-1", "metadata": {}}
        )
        memory_client.client.graph.facts.append(
             {"fact": "MCP Java SDK Research findings", "uuid": "mock-2", "metadata": {}}
        )
        
        # Monkey-patch searching for the test process
        # We need to patch 'search_sessions' because ZepProvider uses 'search_memory' (episodic) by default currently.
        async def mock_search_sessions(self, session_ids, text, limit=10, search_scope="messages", search_type="similarity"):
            # Return a Mock Response object structure that matches what ZepMemoryClient expects
            # client.py expects: resp.sessions[].messages[].content
            
            class MockMessage:
                def __init__(self, content, metadata=None):
                    self.content = content
                    self.metadata = metadata or {}
                    self.score = 0.9

            class MockSession:
                def __init__(self, messages):
                    self.messages = messages

            class MockResponse:
                def __init__(self, sessions):
                    self.sessions = sessions

            # Find matching facts and converting them to "messages" for the search result
            matches = [
                MockMessage(content=f["fact"], metadata=f["uuid"])
                for f in getattr(memory_client.client.graph, "facts", [])
                if text.lower() in f["fact"].lower() or "implementation" in f["fact"].lower()
            ]
            
            return MockResponse(sessions=[MockSession(messages=matches)])

        # Bind the mock method to the instance specifically
        import types
        # Ensure we are patching the mock client's memory object
        memory_client.client.memory.search_sessions = types.MethodType(mock_search_sessions, memory_client.client.memory)



    # Test 2: Zep Provider Context (Mocked by default if Zep down)
    print("\n2. Fetching 'recent_memories' (via Zep)...")
    ctx2 = await store.get_context("recent_memories", params={"topic": "architecture"})
    print(f"Result: {ctx2}")
    
    # Test 3: Engram Self-Reflection (Meta-context)
    print("\n3. Fetching 'engram_project_state' (Self-Reflective)...")
    ctx3 = await store.get_context("engram_project_state", params={"query_focus": "implementation"})
    print(f"Result: {ctx3}")
    assert ctx3["project"] == "Engram"
    assert len(ctx3["implementation_status"]) > 0
    assert "Engram Virtual Context Store implementation plan" in ctx3["implementation_status"][0]

    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    asyncio.run(main())
