
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys

# Mock sys.modules to prevent actual imports of backend dependencies if they fail
# (We want to unit test the tool logic primarily)
# However, to test effectively, we need the actual function. 
# Let's import the tool function from the file.

# Assuming we are running from project root
# We need to mock 'backend.memory.client' and 'backend.workflows.client' BEFORE importing elena

async def verify_delegation():
    print("🧪 Starting Verification: Elena Delegation with Tri-Search")

    # Mocks
    mock_memory_client = AsyncMock()
    # Mock search result
    mock_search_result = MagicMock()
    mock_search_result.content = "Relevant ingestion details about Wiki and Code connectors."
    mock_search_result.metadata = {"source": "wiki.py"}
    mock_memory_client.search_memory.return_value = [mock_search_result]

    mock_execute_story = AsyncMock()
    mock_story_result = MagicMock()
    mock_story_result.success = True
    mock_story_result.story_id = "story-123"
    mock_story_result.story_content = "Once upon a time..."
    mock_story_result.image_path = "/path/to/image.png"
    mock_execute_story.return_value = mock_story_result

    # Patching
    with patch("backend.memory.client.memory_client", mock_memory_client), \
         patch("backend.workflows.client.execute_story", mock_execute_story):
        
        # Import the tool (now that dependencies are patched/mocked)
        # Note: We need to make sure the import sees the mocks.
        # Ideally, we patch where it is imported.
        from backend.agents.elena.agent import delegate_to_sage

        topic = "5 doc types"
        context = "Explain ingestion."

        print(f"👉 triggering delegate_to_sage('{topic}', '{context}')")
        response = await delegate_to_sage(topic, context)

        # Verification 1: Memory Search called?
        mock_memory_client.search_memory.assert_called_once()
        call_args = mock_memory_client.search_memory.call_args
        print(f"✅ Memory Search Called with: {call_args}")
        
        # Verification 2: Execute Story called with enriched context?
        mock_execute_story.assert_called_once()
        story_args = mock_execute_story.call_args
        passed_context = story_args.kwargs.get('context')
        
        if "Retrieved Knowledge" in passed_context and "Relevant ingestion details" in passed_context:
            print("✅ Context Enrichment Successful!")
            print(f"   Enriched Context Preview: {passed_context[:100]}...")
        else:
            print("❌ Context Interaction Failed")
            print(f"   Actual Context: {passed_context}")

        # Verification 3: Response formatting
        if "Sage has completed your request" in response:
             print("✅ Response formatted correctly")
        else:
             print("❌ Unexpected Response format")

if __name__ == "__main__":
    asyncio.run(verify_delegation())
