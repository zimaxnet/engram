
import pytest
from unittest.mock import MagicMock
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from backend.workflows.story_workflow import StoryWorkflow
from backend.workflows.client import StoryWorkflowInput

@pytest.mark.asyncio
async def test_story_workflow_end_to_end():
    """
    Verify the StoryWorkflow executes successfully with mocked activities.
    This ensures the orchestration logic (Story -> Visual -> Save) flows correctly.
    """
    from backend.workflows.story_activities import (
        GenerateStoryOutput,
        GenerateDiagramOutput,
        GenerateImageOutput,
        SaveArtifactsOutput,
        EnrichMemoryOutput
    )

    async with await WorkflowEnvironment.start_time_skipping() as env:
        
        # Mock Activities
        async def mock_generate_story(input):
            return GenerateStoryOutput(
                story_id="test-story-id",
                content="Once upon a time...",
                tokens_used=100,
                success=True
            )
            
        async def mock_generate_image(input):
            return GenerateImageOutput(
                image_data=b"fake_image_bytes",
                success=True
            )

        async def mock_generate_diagram(input):
            return GenerateDiagramOutput(
                 spec={"nodes": []},
                 success=True
            )

        async def mock_save_artifacts(input):
            return SaveArtifactsOutput(
                story_path="/docs/stories/test.md",
                diagram_path="/docs/diagrams/test.json",
                image_path="/docs/images/test.png",
                success=True
            )

        async def mock_enrich_memory(input):
            return EnrichMemoryOutput(
                session_id="session-123",
                success=True
            )

        # Start Worker with mocked activities
        async with Worker(
            env.client,
            task_queue="story-generation-queue",
            workflows=[StoryWorkflow],
            activities={
                "generate_story_activity": mock_generate_story,
                "generate_image_activity": mock_generate_image,
                "generate_diagram_activity": mock_generate_diagram,
                "save_artifacts_activity": mock_save_artifacts,
                "enrich_story_memory_activity": mock_enrich_memory
            },
        ):
            # Execute Workflow
            result = await env.client.execute_workflow(
                StoryWorkflow.run,
                StoryWorkflowInput(
                    user_id="test-user",
                    tenant_id="test-tenant",
                    topic="Test Topic", 
                    include_image=True, 
                    include_diagram=True
                ),
                id="test-workflow-id",
                task_queue="story-generation-queue",
            )
            
            assert result.story_id == "test-story-id"
            assert result.success is True
            assert result.image_path == "/docs/images/test.png"
