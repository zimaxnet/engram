
import pytest
from unittest.mock import MagicMock
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity
from backend.workflows.story_workflow import StoryWorkflow
from backend.workflows.client import StoryWorkflowInput
from backend.workflows.story_activities import (
    GenerateStoryOutput,
    GenerateDiagramOutput,
    GenerateImageOutput,
    SaveArtifactsOutput,
    EnrichMemoryOutput
)

# Mock Activities defined at module level
@activity.defn(name="generate_story_activity")
async def mock_generate_story(input):
    return GenerateStoryOutput(
        story_id="test-story-id",
        content="Once upon a time...",
        tokens_used=100,
        success=True
    )
    
@activity.defn(name="generate_image_activity")
async def mock_generate_image(input):
    return GenerateImageOutput(
        image_data=b"fake_image_bytes",
        success=True
    )

@activity.defn(name="generate_diagram_activity")
async def mock_generate_diagram(input):
    return GenerateDiagramOutput(
         spec={"nodes": []},
         success=True
    )

@activity.defn(name="save_artifacts_activity")
async def mock_save_artifacts(input):
    return SaveArtifactsOutput(
        story_path="/docs/stories/test.md",
        diagram_path="/docs/diagrams/test.json",
        image_path="/docs/images/test.png",
        success=True
    )

@activity.defn(name="enrich_story_memory_activity")
async def mock_enrich_memory(input):
    return EnrichMemoryOutput(
        session_id="session-123",
        success=True
    )

@pytest.mark.asyncio
async def test_story_workflow_end_to_end():
    """
    Verify the StoryWorkflow executes successfully with mocked activities.
    This ensures the orchestration logic (Story -> Visual -> Save) flows correctly.
    """
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Start Worker with mocked activities
        async with Worker(
            env.client,
            task_queue="story-generation-queue",
            workflows=[StoryWorkflow],
            activities=[
                mock_generate_story,
                mock_generate_image,
                mock_generate_diagram,
                mock_save_artifacts,
                mock_enrich_memory
            ],
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
