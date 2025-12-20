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

from backend.core import SecurityContext, get_settings
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


class GraphNodeView(BaseModel):
    id: str
    content: str
    node_type: str
    degree: int = 0
    metadata: dict = {}


class GraphEdgeView(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None
    weight: float = 1.0


class MemoryGraphResponse(BaseModel):
    nodes: list[GraphNodeView]
    edges: list[GraphEdgeView]


async def _build_graph(user_id: str, query: str) -> MemoryGraphResponse:
    from backend.memory.client import memory_client

    facts = await memory_client.get_facts(user_id=user_id, query=query or "", limit=50)

    nodes: dict[str, GraphNodeView] = {}
    edges: list[GraphEdgeView] = []

    def ensure_node(node_id: str, content: str, node_type: str, metadata: dict | None = None) -> None:
        if node_id not in nodes:
            nodes[node_id] = GraphNodeView(
                id=node_id,
                content=content,
                node_type=node_type,
                metadata=metadata or {},
            )

    for fact in facts:
        ensure_node(
            fact.id,
            fact.content,
            getattr(fact, "node_type", "fact") or "fact",
            getattr(fact, "metadata", {}) or {},
        )

    if not nodes:
        sample_id = "fact-sample"
        ensure_node(sample_id, "No facts returned yet", "fact", {})

    meta_keys = {"source", "filename", "etl_source", "tenant_id", "topic", "kind", "role"}

    for fact_node in nodes.values():
        metadata = fact_node.metadata or {}
        for key, raw_value in metadata.items():
            if raw_value is None or key not in meta_keys:
                continue
            values = raw_value if isinstance(raw_value, list) else [raw_value]
            for idx, value in enumerate(values):
                value_str = str(value)
                meta_id = f"meta-{key}-{value_str}".replace(" ", "-")
                ensure_node(meta_id, f"{key}: {value_str}", "entity", {"source": key})
                edge_id = f"edge-{fact_node.id}-{meta_id}-{idx}"
                edges.append(
                    GraphEdgeView(
                        id=edge_id,
                        source=fact_node.id,
                        target=meta_id,
                        label=key,
                        weight=1.0,
                    )
                )

    for edge in edges:
        if edge.source in nodes:
            nodes[edge.source].degree += 1
        if edge.target in nodes:
            nodes[edge.target].degree += 1

    return MemoryGraphResponse(nodes=list(nodes.values()), edges=edges)


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest, user: SecurityContext = Depends(get_current_user)):
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
        results = []

        # 1. Search Facts (Semantic Memory)
        if request.include_facts:
            facts = await memory_client.get_facts(user_id=user.user_id, query=request.query, limit=request.limit)
            for fact in facts:
                results.append(
                    MemoryNode(
                        id=fact.id,
                        content=fact.content,
                        node_type=fact.node_type,
                        confidence=fact.confidence,
                        created_at=fact.created_at,
                        metadata=fact.metadata,
                    )
                )

        # 2. Search Episodes (Episodic Memory)
        if request.include_episodes:
            # use a dummy session_id to trigger the global search logic we added to client.py
            episodes = await memory_client.search_memory(
                session_id="global-search", 
                query=request.query, 
                limit=request.limit
            )
            for ep in episodes:
                # Generate a stable ID for the memory node
                import hashlib
                content_hash = hashlib.md5(ep["content"].encode()).hexdigest()
                
                results.append(
                    MemoryNode(
                        id=f"mem-{content_hash}",
                        content=ep["content"],
                        node_type="episode",
                        confidence=ep.get("score", 0.7),
                        created_at=datetime.utcnow(), # Placeholder as search result might not have timestamp
                        metadata=ep.get("metadata", {}),
                    )
                )

        return MemorySearchResponse(
            results=results,
            total_count=len(results),
            query_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
        )
    except Exception:
        # In tests we want failures to surface (avoid masking contract breaks).
        if get_settings().environment == "test":
            raise
        # Fallback to empty in other environments
        return MemorySearchResponse(
            results=[],
            total_count=0,
            query_time_ms=0,
        )


@router.get("/graph", response_model=MemoryGraphResponse)
async def get_memory_graph(query: str = Query("", max_length=200), user: SecurityContext = Depends(get_current_user)):
    """Return a lightweight knowledge graph for the current user."""
    try:
        return await _build_graph(user.user_id, query)
    except Exception:
        if get_settings().environment == "test":
            raise
        return MemoryGraphResponse(nodes=[], edges=[])


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
    user: SecurityContext = Depends(get_current_user),
):
    """
    List conversation episodes from memory.

    Episodes are discrete conversation sessions that have been
    processed and stored in the knowledge graph.
    """
    try:
        from backend.memory.client import list_episodes as client_list_episodes

        sessions = await client_list_episodes(user_id=user.user_id, limit=limit, offset=offset)

        episodes = []
        for s in sessions:
            episodes.append(
                Episode(
                    id=s["session_id"],
                    summary=s.get("metadata", {}).get("summary", "No summary available"),
                    turn_count=s.get("metadata", {}).get("turn_count", 0),
                    agent_id=s.get("metadata", {}).get("agent_id", "unknown"),
                    started_at=(
                        datetime.fromisoformat(s["created_at"]) if isinstance(s["created_at"], str) else s["created_at"]
                    ),
                    ended_at=(
                        datetime.fromisoformat(s["updated_at"]) if isinstance(s["updated_at"], str) else s["updated_at"]
                    ),
                    topics=s.get("metadata", {}).get("topics", []),
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
async def get_episode_transcript(session_id: str, user: SecurityContext = Depends(get_current_user)):
    """
    Get the detailed transcript for a specific episode.
    """
    try:
        from backend.memory.client import get_session_transcript

        # FUTURE: Verify session belongs to user
        transcript = await get_session_transcript(session_id)

        return EpisodeTranscriptResponse(id=session_id, transcript=transcript)
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
async def add_fact(request: AddFactRequest, user: SecurityContext = Depends(get_current_user)):
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
            metadata={**request.metadata, "type": request.fact_type, "manual": True},
        )

        if fact_id:
            return AddFactResponse(success=True, node_id=fact_id, message="Fact added to knowledge graph")
        else:
            return AddFactResponse(success=False, node_id="", message="Failed to add fact")

    except Exception as e:
        return AddFactResponse(success=False, node_id="", message=f"Error: {str(e)}")
