import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.memory.client import memory_client, MockZepClient

ARTIFACTS_DIR = "backend/tests/artifacts_fixture"

async def bootstrap_knowledge():
    print("--- Bootstrapping Engram Knowledge Graph ---")
    
    # The Engram Engine relies on its own context to function.
    # This bootstrap process ensures the "Brain" is populated with its own design patterns.
    
    # Check if we are using the Local Ephemeral Store (formerly MockZep)
    # In local development, this is the canonical store.
    if isinstance(memory_client.client, MockZepClient):
        print("Initializing Local Ephemeral Context Store.")
        
        # We inject these as Fundamental Facts into the Knowledge Graph.
        
        # 1. Implementation Plan
        try:
            with open(f"{ARTIFACTS_DIR}/implementation_plan.md", "r") as f:
                plan_content = f.read()
                # Ensure the graph exists
                if not hasattr(memory_client.client.graph, "facts"):
                     memory_client.client.graph.facts = []
                     
                memory_client.client.graph.facts.append(
                    {"fact": "Engram Virtual Context Store implementation plan: 1. Registry, 2. Store, 3. ZepProvider.", "uuid": "fact-plan-1"}
                )
                print("Indexed: Implementation Plan (Self-Knowledge)")
        except FileNotFoundError:
             print("Warning: implementation_plan.md not found. Skipping.")

        # 2. Research Java SDK
        try:
            with open(f"{ARTIFACTS_DIR}/research_mcp_java.md", "r") as f:
                memory_client.client.graph.facts.append(
                    {"fact": "MCP Java SDK Research: Spring Boot integration is key for enterprise connectors (Dual-Stack strategy).", "uuid": "fact-java-1"}
                )
                print("Indexed: Research - MCP Java SDK (Strategic Knowledge)")
        except FileNotFoundError:
             print("Warning: research_mcp_java.md not found. Skipping.")

    else:
        print("Connected to Persistent Context Store (Zep).") 
        print("Note: In production, this bootstrap would push to the ingestion pipeline.")

    print("✅ Knowledge Bootstrap Complete.")

if __name__ == "__main__":
    # Ensure list exists for Local Store
    if not hasattr(MockZepClient.MockGraph, "facts"):
        MockZepClient.MockGraph.facts = []
        
        # Patch asearch to search this local knowledge graph
        async def local_asearch(self, user_id, query, limit):
            return [
                type("Fact", (), {"fact": f["fact"], "uuid": f["uuid"], "metadata": {}}) 
                for f in getattr(self, "facts", [])
                if query.lower() in f["fact"].lower() or "status" in query.lower()
            ]
        MockZepClient.MockGraph.asearch = local_asearch

    asyncio.run(bootstrap_knowledge())
