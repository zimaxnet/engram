"""
Memory management endpoints

Provides API for:
- Querying the knowledge graph
- Viewing episodic memory
- Managing semantic facts
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from backend.core import SecurityContext
from backend.api.middleware.auth import get_current_user

router = APIRouter()


class MemoryNode(BaseModel):
    id: str
    content: str
    node_type: str
    confidence: float
    created_at: datetime
    metadata: dict = {}


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 10
    include_episodes: bool = True
    include_facts: bool = True


class MemorySearchResponse(BaseModel):
    results: list[MemoryNode]
    total_count: int
    query_time_ms: float


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest, 
    user: SecurityContext = Depends(get_current_user)
):
    """
    Search the knowledge graph for relevant memories.

    Uses Zep's hybrid retrieval (vector + graph) to find:
    - Relevant facts from the knowledge graph
    - Related episodic memories from past conversations
    """
    try:
        from backend.memory.client import memory_client
        
        start_time = datetime.now()
        
        # Search facts (Semantic Memory) for the authenticated user
        facts = await memory_client.get_facts(
            user_id=user.user_id, 
            query=request.query, 
            limit=request.limit
        )
        
        results = []
        for fact in facts:
            results.append(
                MemoryNode(
                    id=fact.id,
                    content=fact.content,
                    node_type=fact.node_type,
                    confidence=fact.confidence,
                    created_at=fact.created_at,
                    metadata=fact.metadata
                )
            )
            
        return MemorySearchResponse(
            results=results,
            total_count=len(results),
            query_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
        )
    except Exception as e:
        # Fallback to empty
        return MemorySearchResponse(
            results=[],
            total_count=0,
            query_time_ms=0,
        )


class Episode(BaseModel):
    id: str
    summary: str
    turn_count: int
    agent_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    topics: list[str] = []


class EpisodeListResponse(BaseModel):
    episodes: list[Episode]
    total_count: int


@router.get("/episodes", response_model=EpisodeListResponse)
async def list_episodes(
    limit: int = Query(20, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    user: SecurityContext = Depends(get_current_user)
):
    """
    List conversation episodes from memory.

    Episodes are discrete conversation sessions that have been
    processed and stored in the knowledge graph.
    """
    try:
        from backend.memory.client import list_episodes as client_list_episodes
        
        sessions = await client_list_episodes(
            user_id=user.user_id, 
            limit=limit, 
            offset=offset
        )
        
        episodes = []
        for s in sessions:
            episodes.append(
                Episode(
                    id=s["session_id"],
                    summary=s.get("metadata", {}).get("summary", "No summary available"),
                    turn_count=s.get("metadata", {}).get("turn_count", 0),
                    agent_id=s.get("metadata", {}).get("agent_id", "unknown"),
                    started_at=datetime.fromisoformat(s["created_at"]) if isinstance(s["created_at"], str) else s["created_at"],
                    ended_at=datetime.fromisoformat(s["updated_at"]) if isinstance(s["updated_at"], str) else s["updated_at"],
                    topics=s.get("metadata", {}).get("topics", [])
                )
            )
            
        return EpisodeListResponse(
            episodes=episodes,
            total_count=len(episodes),
        )
    except Exception:
        # Fallback return empty
        return EpisodeListResponse(episodes=[], total_count=0)


class EpisodeTranscriptResponse(BaseModel):
    id: str
    transcript: list[dict]


@router.get("/episodes/{session_id}", response_model=EpisodeTranscriptResponse)
async def get_episode_transcript(
    session_id: str,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Get the detailed transcript for a specific episode.
    """
    try:
        from backend.memory.client import get_session_transcript
        
        # FUTURE: Verify session belongs to user
        transcript = await get_session_transcript(session_id)
        
        return EpisodeTranscriptResponse(
            id=session_id,
            transcript=transcript
        )
    except Exception:
        # Fallback
        return EpisodeTranscriptResponse(id=session_id, transcript=[])


class AddFactRequest(BaseModel):
    content: str
    fact_type: str = "custom"
    confidence: float = 1.0
    metadata: dict = {}


class AddFactResponse(BaseModel):
    success: bool
    node_id: str
    message: str


@router.post("/facts", response_model=AddFactResponse)
async def add_fact(
    request: AddFactRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Manually add a fact to the knowledge graph.

    Facts added this way are marked as user-provided
    and given high confidence by default.
    """
    try:
        from backend.memory.client import memory_client
        
        fact_id = await memory_client.add_fact(
            user_id=user.user_id, 
            fact=request.content,
            metadata={**request.metadata, "type": request.fact_type, "manual": True}
        )
        
        if fact_id:
            return AddFactResponse(
                success=True, node_id=fact_id, message="Fact added to knowledge graph"
            )
        else:
            return AddFactResponse(
                success=False, node_id="", message="Failed to add fact"
            )
            
    except Exception as e:
         return AddFactResponse(
            success=False, node_id="", message=f"Error: {str(e)}"
        )
