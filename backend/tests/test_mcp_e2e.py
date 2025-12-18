
import pytest
import uuid
from unittest.mock import AsyncMock, patch

from backend.core import EnterpriseContext, SecurityContext, Role
from backend.api.routers.mcp_server import mcp_server, _sessions




@pytest.mark.asyncio
async def test_mcp_chat_tool_basic(mock_agent_services):
    """Test basic chat tool execution"""
    # 1. Clear sessions
    _sessions.clear()

    # 2. Call tool
    result = await mcp_server.call_tool(
        "chat_with_agent", 
        arguments={"message": "Hello MCP"}
    )

    # 3. Verify Result
    print(f"\nDEBUG: Result Type: {type(result)}")
    print(f"DEBUG: Result: {result}")
    
    # Handling potential nested list structure from call_tool
    # If result[0] is a list, likely result is [[TextContent]]
    text_content = ""
    if isinstance(result, list):
        if len(result) > 0:
            first = result[0]
            if isinstance(first, list) and len(first) > 0:
                text_content = getattr(first[0], 'text', str(first[0]))
            else:
                text_content = getattr(first, 'text', str(first))
    else:
        text_content = str(result)
        
    assert "MCP Response to: Hello MCP" in text_content
    
    # 4. Verify Session Created
    assert len(_sessions) == 1


@pytest.mark.asyncio
async def test_mcp_chat_session_persistence(mock_agent_services):
    """Test session persistence in MCP tool"""
    _sessions.clear()
    session_id = str(uuid.uuid4())

    # 1. First msg
    await mcp_server.call_tool(
        "chat_with_agent", 
        arguments={"message": "Hi", "session_id": session_id}
    )

    # 2. Verify Session
    assert session_id in _sessions
    first_context = _sessions[session_id]

    # 3. Second msg
    await mcp_server.call_tool(
        "chat_with_agent", 
        arguments={"message": "Again", "session_id": session_id}
    )

    # 4. Verify same session used
    assert _sessions[session_id] is first_context  # Object identity might differ but ID same
    assert _sessions[session_id].episodic.conversation_id == session_id


@pytest.mark.asyncio
async def test_mcp_context_resource():
    """Test context resource reading"""
    result = await mcp_server.read_resource("context://current")
    assert "Engram MCP Context: Active" in str(result)
