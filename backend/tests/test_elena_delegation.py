import pytest
from unittest.mock import MagicMock, AsyncMock
from backend.agents.elena.agent import ElenaAgent
@pytest.mark.asyncio
async def test_elena_selects_delegation_for_visual_requests():
    """
    Verify that Elena's tool selection logic correctly identifies requests
    needs visualization/story creation and selects the 'delegate_to_sage' tool.
    """
    agent = ElenaAgent()
    
    # CASE 1: Explicit Visual Request
    # "Create a story about Mars and show me a visual."
    user_input = "Create a story about Mars and show me a visual."
    tool_name, tool_args = agent._select_tool(user_input)
    
    assert tool_name == "delegate_to_sage"
    assert "topic" in tool_args
    assert "Mars" in tool_args["topic"]

    # CASE 2: Diagram Request
    user_input = "Generate a sequence diagram for the login flow."
    tool_name, tool_args = agent._select_tool(user_input)
    
    assert tool_name == "delegate_to_sage"
    assert tool_args["context"] == user_input

    # CASE 3: Non-delegated Request (should default to None or other tool)
    user_input = "Analyze these requirements."
    tool_name, tool_args = agent._select_tool(user_input)
    
    # expected to be analyze_requirements or None (depending on keyword match)
    # logic: "Analyze" -> possibly analyze_requirements if keywords match capabilities
    # let's check strict "delegate" mismatch
    assert tool_name != "delegate_to_sage"
 
