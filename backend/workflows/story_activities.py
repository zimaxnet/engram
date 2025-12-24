"""
Story Activities

Temporal activities for story generation workflow.
These are the atomic units of work that can fail and retry independently.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from temporalio import activity

logger = logging.getLogger(__name__)


# =============================================================================
# Activity Input/Output Types
# =============================================================================


@dataclass
class GenerateStoryInput:
    """Input for story generation activity"""
    topic: str
    context: Optional[str] = None


@dataclass
class GenerateStoryOutput:
    """Output from story generation activity"""
    story_id: str
    content: str
    tokens_used: int
    success: bool
    error: Optional[str] = None


@dataclass
class GenerateDiagramInput:
    """Input for diagram generation activity"""
    topic: str
    diagram_type: str = "architecture"


@dataclass
class GenerateDiagramOutput:
    """Output from diagram generation activity"""
    spec: Optional[dict]
    success: bool
    error: Optional[str] = None


@dataclass
class GenerateImageInput:
    """Input for image generation activity"""
    prompt: str


@dataclass
class GenerateImageOutput:
    """Output from image generation activity"""
    image_data: bytes
    success: bool
    error: Optional[str] = None


@dataclass
class SaveArtifactsInput:
    """Input for saving artifacts"""
    story_id: str
    topic: str
    story_content: str
    diagram_spec: Optional[dict] = None
    image_data: Optional[bytes] = None


@dataclass
class SaveArtifactsOutput:
    """Output from saving artifacts"""
    story_path: Optional[str]
    diagram_path: Optional[str]
    image_path: Optional[str]
    success: bool
    error: Optional[str] = None


@dataclass
class EnrichMemoryInput:
    """Input for memory enrichment"""
    user_id: str
    story_id: str
    topic: str
    content: str
    image_path: Optional[str] = None


@dataclass
class EnrichMemoryOutput:
    """Output from memory enrichment"""
    session_id: Optional[str]
    success: bool
    error: Optional[str] = None


# =============================================================================
# Activities
# =============================================================================


@activity.defn
async def generate_story_activity(input: GenerateStoryInput) -> GenerateStoryOutput:
    """
    Generate a story using Claude.
    
    This is the primary LLM activity — may take 30-120 seconds.
    """
    activity.logger.info(f"Generating story: {input.topic}")
    
    try:
        from backend.llm.claude_client import get_claude_client
        
        client = get_claude_client()
        content = await client.generate_story(
            topic=input.topic,
            context=input.context,
        )
        
        # Generate story ID
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = input.topic.lower().replace(" ", "-").replace("_", "-")[:50]
        story_id = f"{timestamp}-{slug}"
        
        activity.logger.info(f"Story generated: {len(content)} chars")
        
        return GenerateStoryOutput(
            story_id=story_id,
            content=content,
            tokens_used=len(content) // 4,  # Rough estimate
            success=True,
        )
        
    except Exception as e:
        activity.logger.error(f"Story generation failed: {e}")
        return GenerateStoryOutput(
            story_id="",
            content="",
            tokens_used=0,
            success=False,
            error=str(e),
        )


@activity.defn
async def generate_diagram_activity(input: GenerateDiagramInput) -> GenerateDiagramOutput:
    """
    Generate a diagram specification using Gemini.
    
    Returns a Nano Banana Pro compatible JSON spec.
    """
    activity.logger.info(f"Generating diagram: {input.topic}")
    
    try:
        from backend.llm.gemini_client import get_gemini_client
        
        client = get_gemini_client()
        spec = await client.generate_diagram_spec(
            topic=input.topic,
            diagram_type=input.diagram_type,
        )
        
        activity.logger.info("Diagram spec generated")
        
        return GenerateDiagramOutput(
            spec=spec,
            success=True,
        )
        
    except Exception as e:
        activity.logger.error(f"Diagram generation failed: {e}")
        return GenerateDiagramOutput(
            spec=None,
            success=False,
            error=str(e),
        )


@activity.defn
async def generate_image_activity(input: GenerateImageInput) -> GenerateImageOutput:
    """
    Generate an image using Gemini/Imagen.
    """
    activity.logger.info(f"Generating image for prompt: {input.prompt[:50]}...")
    
    try:
        from backend.llm.gemini_client import get_gemini_client
        
        client = get_gemini_client()
        image_data = await client.generate_image(prompt=input.prompt)
        
        if not image_data:
             return GenerateImageOutput(image_data=b"", success=False, error="Empty image data returned")

        activity.logger.info(f"Image generated: {len(image_data)} bytes")
        
        return GenerateImageOutput(
            image_data=image_data,
            success=True,
        )
        
    except Exception as e:
        activity.logger.error(f"Image generation failed: {e}")
        return GenerateImageOutput(
            image_data=b"",
            success=False,
            error=str(e),
        )


@activity.defn
async def save_artifacts_activity(input: SaveArtifactsInput) -> SaveArtifactsOutput:
    """
    Save story and diagram to the docs folder (OneDrive sync).
    """
    activity.logger.info(f"Saving artifacts: {input.story_id}")
    
    try:
        from backend.core import get_settings
        
        settings = get_settings()
        docs_path = Path(settings.onedrive_docs_path or "docs")
        
        # Create directories
        stories_dir = docs_path / "stories"
        diagrams_dir = docs_path / "diagrams"
        images_dir = docs_path / "images"
        stories_dir.mkdir(parents=True, exist_ok=True)
        diagrams_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Save story
        story_filename = f"{input.story_id}.md"
        story_path = stories_dir / story_filename
        story_path.write_text(input.story_content, encoding="utf-8")
        
        # Save diagram if present
        diagram_path = None
        if input.diagram_spec:
            diagram_filename = f"{input.story_id}.json"
            diagram_file = diagrams_dir / diagram_filename
            diagram_file.write_text(json.dumps(input.diagram_spec, indent=2), encoding="utf-8")
            diagram_path = str(diagram_file)
            
        # Save image if present
        image_path = None
        if input.image_data:
            image_filename = f"{input.story_id}.png"
            image_file = images_dir / image_filename
            image_file.write_bytes(input.image_data)
            image_path = str(image_file)
        
        activity.logger.info(f"Artifacts saved: {story_path}")
        
        return SaveArtifactsOutput(
            story_path=str(story_path),
            diagram_path=diagram_path,
            image_path=image_path,
            success=True,
        )
        
    except Exception as e:
        activity.logger.error(f"Failed to save artifacts: {e}")
        return SaveArtifactsOutput(
            story_path=None,
            diagram_path=None,
            image_path=None,
            success=False,
            error=str(e),
        )


@activity.defn
async def enrich_story_memory_activity(input: EnrichMemoryInput) -> EnrichMemoryOutput:
    """
    Store story content in Zep memory for future reference.
    """
    activity.logger.info(f"Enriching memory: {input.story_id}")
    
    try:
        from backend.memory.client import memory_client
        
        session_id = f"story-{input.story_id}"
        
        await memory_client.add_session(
            session_id=session_id,
            user_id=input.user_id,
            metadata={
                "title": input.topic,
                "type": "story",
                "story_id": input.story_id,
                "image_path": input.image_path,
                "created_at": datetime.now().isoformat(),
            }
        )
        
        await memory_client.add_messages(
            session_id=session_id,
            messages=[{
                "role": "assistant",
                "content": input.content,
                "metadata": {"agent_id": "sage", "topic": input.topic},
            }]
        )
        
        activity.logger.info(f"Memory enriched: {session_id}")
        
        return EnrichMemoryOutput(
            session_id=session_id,
            success=True,
        )
        
    except Exception as e:
        activity.logger.error(f"Memory enrichment failed: {e}")
        return EnrichMemoryOutput(
            session_id=None,
            success=False,
            error=str(e),
        )
