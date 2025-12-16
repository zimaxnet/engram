
import pytest
from backend.api.routers.mcp import mcp_server

@pytest.mark.asyncio
async def test_mcp_enrich_memory(mock_agent_services):
    """Test enrich_memory tool"""
    result = await mcp_server.call_tool(
        "enrich_memory", 
        arguments={"text": "New fact"}
    )
    # Debug print
    print(f"DEBUG Enrich Result: {result}")
    
    # Assuming result is list of TextContent or just string?
    # Based on previous error, likely a list.
    if isinstance(result, list):
         # Check if any content item has the text
         found = any("Memory enriched successfully." in (getattr(item, 'text', '') or str(item)) for item in result)
         assert found
    else:
         assert "Memory enriched successfully." in str(result)

@pytest.mark.asyncio
async def test_mcp_search_memory(mock_agent_services):
    """Test search_memory tool"""
    result = await mcp_server.call_tool(
        "search_memory", 
        arguments={"query": "test query"}
    )
    # Simulation returns string
    text_result = str(result) if not isinstance(result, list) else result[0].text
    assert "Memory search for 'test query' initiated" in text_result

@pytest.mark.asyncio
async def test_mcp_voice_config(mock_agent_services):
    """Test get_voice_config tool"""
    # Verify it returns configuration string
    result = await mcp_server.call_tool(
        "get_voice_config", 
        arguments={"agent_id": "elena"}
    )
    # Should return config info
    text_result = str(result)
    assert "Agent: elena" in text_result
    assert "Voice:" in text_result
