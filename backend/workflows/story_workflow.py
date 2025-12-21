"""
Story Workflow

Temporal workflow for Sage's story generation tasks.
Provides durable execution for the multi-step storytelling process:

1. Generate story with Claude (can take 30-120s)
2. Generate diagram spec with Gemini
3. Save artifacts to OneDrive (docs folder)
4. Enrich Zep memory with story content
5. Return completed story package

This ensures story generation survives crashes and can be monitored/queried.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities (with sandbox warning suppression)
with workflow.unsafe.imports_passed_through():
    from backend.workflows.story_activities import (
        GenerateStoryInput,
        GenerateDiagramInput,
        SaveArtifactsInput,
        EnrichMemoryInput,
        generate_story_activity,
        generate_diagram_activity,
        save_artifacts_activity,
        enrich_story_memory_activity,
    )


logger = logging.getLogger(__name__)


# =============================================================================
# Workflow Input/Output
# =============================================================================


@dataclass
class StoryWorkflowInput:
    """Input to start a story workflow"""
    
    user_id: str
    tenant_id: str
    topic: str
    context: Optional[str] = None
    include_diagram: bool = True
    diagram_type: str = "architecture"


@dataclass
class StoryWorkflowOutput:
    """Output from story workflow"""
    
    story_id: str
    topic: str
    story_content: str
    story_path: Optional[str] = None
    diagram_spec: Optional[dict] = None
    diagram_path: Optional[str] = None
    memory_session_id: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    tokens_used: int = 0


# =============================================================================
# Retry Policies
# =============================================================================

# Policy for LLM calls (Claude/Gemini) - longer timeout, more retries
LLM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
)

# Policy for file/memory operations - fewer retries
STORAGE_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
)


# =============================================================================
# Story Workflow
# =============================================================================


@workflow.defn
class StoryWorkflow:
    """
    Durable workflow for story generation.
    
    This workflow orchestrates the complete story creation process:
    1. Generate story content using Claude
    2. Generate diagram specification using Gemini (optional)
    3. Save artifacts to docs folder (OneDrive sync)
    4. Enrich Zep memory with story content
    
    The workflow is fully resumable — if it fails at any step,
    it will retry from that point with the retry policy.
    """
    
    def __init__(self):
        self._story_content: Optional[str] = None
        self._diagram_spec: Optional[dict] = None
        self._story_path: Optional[str] = None
        self._diagram_path: Optional[str] = None
        self._status: str = "starting"
        self._progress: int = 0
    
    # -------------------------------------------------------------------------
    # Query Handlers
    # -------------------------------------------------------------------------
    
    @workflow.query
    def get_status(self) -> str:
        """Query current workflow status"""
        return self._status
    
    @workflow.query
    def get_progress(self) -> int:
        """Query progress percentage (0-100)"""
        return self._progress
    
    @workflow.query
    def get_story_preview(self) -> Optional[str]:
        """Get first 500 characters of story (for progress UI)"""
        if self._story_content:
            return self._story_content[:500]
        return None
    
    # -------------------------------------------------------------------------
    # Main Workflow
    # -------------------------------------------------------------------------
    
    @workflow.run
    async def run(self, input: StoryWorkflowInput) -> StoryWorkflowOutput:
        """
        Execute the story generation workflow.
        
        This is the durable execution path that survives crashes.
        """
        workflow.logger.info(f"Starting story workflow: topic='{input.topic}'")
        
        story_id = ""
        memory_session_id = None
        tokens_used = 0
        
        try:
            # Step 1: Generate Story with Claude (40% of progress)
            self._status = "generating_story"
            self._progress = 10
            
            workflow.logger.info("Step 1: Generating story with Claude...")
            
            story_result = await workflow.execute_activity(
                generate_story_activity,
                GenerateStoryInput(
                    topic=input.topic,
                    context=input.context,
                ),
                start_to_close_timeout=timedelta(minutes=3),  # Claude can be slow
                retry_policy=LLM_RETRY_POLICY,
            )
            
            if not story_result.success:
                return StoryWorkflowOutput(
                    story_id="",
                    topic=input.topic,
                    story_content="",
                    success=False,
                    error=story_result.error,
                )
            
            self._story_content = story_result.content
            story_id = story_result.story_id
            tokens_used += story_result.tokens_used
            self._progress = 40
            
            workflow.logger.info(f"Story generated: {len(self._story_content)} chars")
            
            # Step 2: Generate Diagram with Gemini (optional, 25% of progress)
            if input.include_diagram:
                self._status = "generating_diagram"
                self._progress = 50
                
                workflow.logger.info("Step 2: Generating diagram with Gemini...")
                
                diagram_result = await workflow.execute_activity(
                    generate_diagram_activity,
                    GenerateDiagramInput(
                        topic=input.topic,
                        diagram_type=input.diagram_type,
                    ),
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=LLM_RETRY_POLICY,
                )
                
                if diagram_result.success:
                    self._diagram_spec = diagram_result.spec
                    workflow.logger.info("Diagram spec generated")
                else:
                    workflow.logger.warning(f"Diagram generation failed: {diagram_result.error}")
                    # Continue without diagram — not fatal
                
                self._progress = 65
            else:
                self._progress = 65
            
            # Step 3: Save Artifacts (20% of progress)
            self._status = "saving_artifacts"
            
            workflow.logger.info("Step 3: Saving artifacts to docs folder...")
            
            save_result = await workflow.execute_activity(
                save_artifacts_activity,
                SaveArtifactsInput(
                    story_id=story_id,
                    topic=input.topic,
                    story_content=self._story_content,
                    diagram_spec=self._diagram_spec,
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=STORAGE_RETRY_POLICY,
            )
            
            if save_result.success:
                self._story_path = save_result.story_path
                self._diagram_path = save_result.diagram_path
                workflow.logger.info(f"Artifacts saved: {save_result.story_path}")
            else:
                workflow.logger.warning(f"Failed to save artifacts: {save_result.error}")
            
            self._progress = 85
            
            # Step 4: Enrich Memory (15% of progress)
            self._status = "enriching_memory"
            
            workflow.logger.info("Step 4: Enriching Zep memory...")
            
            memory_result = await workflow.execute_activity(
                enrich_story_memory_activity,
                EnrichMemoryInput(
                    user_id=input.user_id,
                    story_id=story_id,
                    topic=input.topic,
                    content=self._story_content[:5000],  # Truncate for memory
                ),
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=STORAGE_RETRY_POLICY,
            )
            
            if memory_result.success:
                memory_session_id = memory_result.session_id
                workflow.logger.info(f"Memory enriched: {memory_session_id}")
            else:
                workflow.logger.warning(f"Memory enrichment failed: {memory_result.error}")
            
            self._progress = 100
            self._status = "completed"
            
            # Success!
            workflow.logger.info(f"Story workflow completed: {story_id}")
            
            return StoryWorkflowOutput(
                story_id=story_id,
                topic=input.topic,
                story_content=self._story_content,
                story_path=self._story_path,
                diagram_spec=self._diagram_spec,
                diagram_path=self._diagram_path,
                memory_session_id=memory_session_id,
                success=True,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            workflow.logger.error(f"Story workflow failed: {e}")
            self._status = "failed"
            
            return StoryWorkflowOutput(
                story_id=story_id,
                topic=input.topic,
                story_content=self._story_content or "",
                success=False,
                error=str(e),
            )
