import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.context.registry import register_context
from backend.api.routers.mcp_server import get_context, list_contexts

# Define a test context to ensure registry has data
@register_context(name="mcp_test_context", description="Test context for MCP exposure")
async def mcp_test_func(param1: str):
    return {"status": "ok", "param_received": param1}

async def main():
    print("--- Testing MCP Context Exposure ---")

    # 1. Test List Contexts
    print("\n1. Listing Contexts...")
    listing = await list_contexts()
    print(listing)
    assert "mcp_test_context" in listing

    # 2. Test Get Context (Tool)
    print("\n2. Getting Context via Tool...")
    # FastMCP tools pass arguments by name
    import json
    # Simulate the call. The tool signature is get_context(name, params: str)
    params_json = json.dumps({"param1": "hello_mcp"})
    result = await get_context(name="mcp_test_context", params=params_json)
    print(result)
    assert "hello_mcp" in result
    
    print("\n✅ MCP Exposure Verification Successful!")

if __name__ == "__main__":
    asyncio.run(main())
