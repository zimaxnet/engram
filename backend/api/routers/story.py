"""
Story API Router

Endpoints for Sage Meridian's story generation and diagram creation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.middleware.rbac import get_current_user
from backend.core import SecurityContext, EnterpriseContext, get_settings
from backend.agents.sage import sage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["story"])


# =============================================================================
# Request/Response Models
# =============================================================================


class StoryCreateRequest(BaseModel):
    """Request to create a new story."""
    topic: str
    context: Optional[str] = None
    include_diagram: bool = True
    diagram_type: str = "architecture"


class StoryResponse(BaseModel):
    """Response containing story and optional diagram."""
    story_id: str
    topic: str
    story_content: str
    story_path: Optional[str] = None
    diagram_spec: Optional[dict] = None
    diagram_path: Optional[str] = None
    image_path: Optional[str] = None
    created_at: str


class StoryListItem(BaseModel):
    """Summary of a story for listing."""
    story_id: str
    topic: str
    created_at: str
    story_path: str


# =============================================================================
# Helper Functions
# =============================================================================


def _get_stories_dir() -> Path:
    """Get the stories directory path."""
    settings = get_settings()
    docs_path = Path(settings.onedrive_docs_path or "docs")
    stories_dir = docs_path / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    return stories_dir


def _get_diagrams_dir() -> Path:
    """Get the diagrams directory path."""
    settings = get_settings()
    docs_path = Path(settings.onedrive_docs_path or "docs")
    diagrams_dir = docs_path / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    return diagrams_dir


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/create", response_model=StoryResponse)
async def create_story(
    request: StoryCreateRequest,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Create a new story and optional diagram via Temporal workflow.
    
    Uses durable execution for the multi-step process:
    1. Generate story with Claude
    2. Generate diagram spec with Gemini
    3. Save artifacts to docs folder (OneDrive sync)
    4. Enrich Zep memory
    
    The workflow survives crashes and can be monitored.
    """
    try:
        from backend.workflows.client import execute_story
        
        logger.info(f"Creating story via Temporal: {request.topic}")
        
        # Execute via Temporal workflow for durability
        result = await execute_story(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            topic=request.topic,
            context=request.context,
            include_diagram=request.include_diagram,
            include_image=True, # Always include image for now, or add to request model
            diagram_type=request.diagram_type,
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return StoryResponse(
            story_id=result.story_id,
            topic=result.topic,
            story_content=result.story_content,
            story_path=result.story_path,
            diagram_spec=result.diagram_spec,
            diagram_path=result.diagram_path,
            image_path=f"/api/v1/images/{result.story_id}.png" if (await _check_image_exists(result.story_id)) else None,
            created_at=datetime.now().isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating story: {e}")
        # Fallback to direct execution if Temporal unavailable
        logger.warning("Falling back to direct execution (Temporal may be unavailable)")
        return await _create_story_direct(request, user)


async def _check_image_exists(story_id: str) -> bool:
    """Check if an image exists for the story."""
    settings = get_settings()
    docs_path = Path(settings.onedrive_docs_path or "docs")
    image_path = docs_path / "images" / f"{story_id}.png"
    return image_path.exists()


async def _create_story_direct(request: StoryCreateRequest, user: SecurityContext) -> StoryResponse:
    """
    Direct story creation (fallback when Temporal is unavailable).
    """
    from backend.llm.claude_client import get_claude_client
    from backend.llm.gemini_client import get_gemini_client
    
    # Generate story using Claude
    logger.info(f"Creating story directly: {request.topic}")
    claude = get_claude_client()
    story_content = await claude.generate_story(
        topic=request.topic,
        context=request.context,
    )
    
    # Generate diagram if requested
    diagram_spec = None
    if request.include_diagram:
        logger.info(f"Creating diagram: {request.topic}")
        gemini = get_gemini_client()
        diagram_spec = await gemini.generate_diagram_spec(
            topic=request.topic,
            diagram_type=request.diagram_type,
        )
        
    # Generate image (always for simplicity in fallback)
    logger.info(f"Creating image: {request.topic}")
    gemini_client = get_gemini_client()
    try:
        image_data = await gemini_client.generate_image(prompt=request.topic)
    except Exception as e:
        logger.error(f"Failed to generate image in direct mode: {e}")
        image_data = None
    
    # Generate file paths
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = request.topic.lower().replace(" ", "-").replace("_", "-")[:50]
    story_id = f"{timestamp}-{slug}"
    
    # Save story
    stories_dir = _get_stories_dir()
    story_filename = f"{story_id}.md"
    story_path = stories_dir / story_filename
    story_path.write_text(story_content, encoding="utf-8")
    
    # Save diagram
    diagram_path = None
    if diagram_spec:
        diagrams_dir = _get_diagrams_dir()
        diagram_filename = f"{story_id}.json"
        diagram_file = diagrams_dir / diagram_filename
        diagram_file.write_text(json.dumps(diagram_spec, indent=2), encoding="utf-8")
        diagram_path = str(diagram_file)
        
    # Save image
    image_path_str = None
    if image_data:
        docs_path = Path(get_settings().onedrive_docs_path or "docs")
        images_dir = docs_path / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        image_filename = f"{story_id}.png"
        image_file = images_dir / image_filename
        image_file.write_bytes(image_data)
        image_path_str = f"/api/v1/images/{story_id}.png"
    
    # Enrich memory
    try:
        from backend.memory.client import memory_client
        
        session_id = f"story-{story_id}"
        await memory_client.add_session(
            session_id=session_id,
            user_id=user.user_id,
            metadata={
                "title": request.topic,
                "type": "story",
                "story_id": story_id,
                "image_path": image_path_str,
                "created_at": datetime.now().isoformat(),
            }
        )
        await memory_client.add_messages(
            session_id=session_id,
            messages=[{
                "role": "assistant",
                "content": story_content[:5000],
                "metadata": {"agent_id": "sage", "topic": request.topic},
            }]
        )
    except Exception as e:
        logger.warning(f"Failed to enrich memory: {e}")
    
    return StoryResponse(
        story_id=story_id,
        topic=request.topic,
        story_content=story_content,
        story_path=str(story_path),
        diagram_spec=diagram_spec,
        diagram_path=diagram_path,
        image_path=image_path_str,
        created_at=datetime.now().isoformat(),
    )


@router.get("/latest", response_model=StoryResponse)
async def get_latest_story(user: SecurityContext = Depends(get_current_user)):
    """Get the most recently created story."""
    stories_dir = _get_stories_dir()
    
    story_files = sorted(stories_dir.glob("*.md"), reverse=True)
    if not story_files:
        raise HTTPException(status_code=404, detail="No stories found")
    
    latest = story_files[0]
    story_id = latest.stem
    
    # Try to load corresponding diagram
    diagrams_dir = _get_diagrams_dir()
    diagram_path = diagrams_dir / f"{story_id}.json"
    diagram_spec = None
    if diagram_path.exists():
        diagram_spec = json.loads(diagram_path.read_text())
    
    # Check for image
    image_path_str = None
    if (stories_dir.parent / "images" / f"{story_id}.png").exists():
        image_path_str = f"/api/v1/images/{story_id}.png"
    
    return StoryResponse(
        story_id=story_id,
        topic=story_id.split("-", 2)[-1].replace("-", " ") if "-" in story_id else story_id,
        story_content=latest.read_text(),
        story_path=str(latest),
        diagram_spec=diagram_spec,
        diagram_path=str(diagram_path) if diagram_path.exists() else None,
        image_path=image_path_str,
        created_at=latest.stat().st_mtime.__str__(),
    )


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str, user: SecurityContext = Depends(get_current_user)):
    """Get a specific story by ID."""
    stories_dir = _get_stories_dir()
    story_path = stories_dir / f"{story_id}.md"
    
    if not story_path.exists():
        raise HTTPException(status_code=404, detail=f"Story not found: {story_id}")
    
    # Try to load corresponding diagram
    diagrams_dir = _get_diagrams_dir()
    diagram_path = diagrams_dir / f"{story_id}.json"
    diagram_spec = None
    if diagram_path.exists():
        diagram_spec = json.loads(diagram_path.read_text())
    
    # Check for image
    image_path_str = None
    if (stories_dir.parent / "images" / f"{story_id}.png").exists():
        image_path_str = f"/api/v1/images/{story_id}.png"
    
    return StoryResponse(
        story_id=story_id,
        topic=story_id.split("-", 2)[-1].replace("-", " ") if "-" in story_id else story_id,
        story_content=story_path.read_text(),
        story_path=str(story_path),
        diagram_spec=diagram_spec,
        diagram_path=str(diagram_path) if diagram_path.exists() else None,
        image_path=image_path_str,
        created_at=story_path.stat().st_mtime.__str__(),
    )


@router.get("/", response_model=list[StoryListItem])
async def list_stories(user: SecurityContext = Depends(get_current_user)):
    """List all available stories."""
    stories_dir = _get_stories_dir()
    
    stories = []
    for story_file in sorted(stories_dir.glob("*.md"), reverse=True):
        story_id = story_file.stem
        stories.append(StoryListItem(
            story_id=story_id,
            topic=story_id.split("-", 2)[-1].replace("-", " ") if "-" in story_id else story_id,
            created_at=story_file.stat().st_mtime.__str__(),
            story_path=str(story_file),
        ))
    
    return stories
