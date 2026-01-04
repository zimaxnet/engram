"""
Memory management endpoints

Provides API for:
- Querying the knowledge graph
- Viewing episodic memory
- Managing semantic facts
- AI Agent access via API key
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, Depends, HTTPException, Header
from pydantic import BaseModel

from backend.core import SecurityContext, get_settings
from backend.api.middleware.auth import get_current_user

router = APIRouter()


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """Verify API key for AI agent access (lighter than full Entra ID auth)."""
    settings = get_settings()
    # Accept the configured Azure AI Key as a valid agent API key
    if x_api_key and settings.azure_ai_key and x_api_key == settings.azure_ai_key:
        return "agent-api"
    raise HTTPException(status_code=401, detail="Invalid or missing API key")


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

    # 1. Try to get Semantic Facts (Zep Cloud feature)
    try:
        facts = await memory_client.get_facts(user_id=user_id, query=query or "", limit=50)
        for fact in facts:
            ensure_node(
                fact.id,
                fact.content,
                getattr(fact, "node_type", "fact") or "fact",
                getattr(fact, "metadata", {}) or {},
            )
    except Exception:
        # Ignore errors from Zep Cloud endpoints if getting facts fails
        pass

    # 2. Build Graph from Episodic Memory (Sessions & Topics)
    # This works with Zep OSS v0.x and provides an "Episode Graph"
    try:
        # Get recent sessions
        sessions = await memory_client.list_sessions(user_id=user_id, limit=20)
        
        for sess in sessions:
            sess_id = sess.get("session_id")
            meta = sess.get("metadata", {})
            summary = meta.get("summary", "Conversation")
            topics = meta.get("topics", [])
            
            # Create Episode Node
            # Use a short label for the node, full summary in metadata
            label = f"Ep: {sess_id[:8]}..."
            if summary and len(summary) > 20: 
                 label = summary[:30] + "..."
            elif summary:
                 label = summary
                 
            ensure_node(
                node_id=sess_id,
                content=label,
                node_type="memory", # Valid types: fact, memory, entity
                metadata={"full_content": summary, "timestamp": sess.get("created_at")},
            )
            
            # Create Topic Nodes and Edges
            for topic in topics:
                topic_id = f"topic-{topic.lower().replace(' ', '-')}"
                ensure_node(
                    node_id=topic_id,
                    content=topic,
                    node_type="entity", 
                    metadata={"kind": "topic"},
                )
                
                # Link Episode to Topic
                edge_id = f"edge-{sess_id}-{topic_id}"
                edges.append(
                    GraphEdgeView(
                        id=edge_id,
                        source=sess_id,
                        target=topic_id,
                        label="concerns",
                        weight=1.0,
                    )
                )
                
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to build episode graph: {e}")

    # 3. Create Fact-Metadata Edges (for existing facts)
    meta_keys = {"source", "filename", "etl_source", "tenant_id", "topic", "kind", "role"}
    
    # We iterate over a copy of values because we might add new nodes
    existing_nodes = list(nodes.values()) 
    for node in existing_nodes:
        if node.node_type != "fact": continue
        
        metadata = node.metadata or {}
        for key, raw_value in metadata.items():
            if raw_value is None or key not in meta_keys:
                continue
            values = raw_value if isinstance(raw_value, list) else [raw_value]
            for idx, value in enumerate(values):
                value_str = str(value)
                meta_id = f"meta-{key}-{value_str}".replace(" ", "-")
                ensure_node(meta_id, f"{key}: {value_str}", "entity", {"source": key})
                edge_id = f"edge-{node.id}-{meta_id}-{idx}"
                edges.append(
                    GraphEdgeView(
                        id=edge_id,
                        source=node.id,
                        target=meta_id,
                        label=key,
                        weight=1.0,
                    )
                )

    if not nodes:
        sample_id = "fact-sample"
        ensure_node(sample_id, "No data available. Start chatting to generate memory.", "fact", {})

    # Calculate degrees
    for edge in edges:
        if edge.source in nodes:
            nodes[edge.source].degree += 1
        if edge.target in nodes:
            nodes[edge.target].degree += 1

    return MemoryGraphResponse(nodes=list(nodes.values()), edges=edges)


@router.post("/search/public", response_model=MemorySearchResponse)
async def search_memory_public(
    request: MemorySearchRequest, 
    api_key: str = Depends(verify_api_key)
):
    """
    Public search endpoint for AI Agents (Cursor, Windsurf, etc).
    Protected by X-API-Key header.
    Hardcoded to search 'user-derek' memory for now (single user mode).
    """
    # Create a dummy security context for the agent
    # In single-user mode, agents act on behalf of the primary user
    user = SecurityContext(
        user_id="user-derek",
        tenant_id="default-tenant",
        roles=["agent"],
        is_authenticated=True
    )
    return await search_memory(request, user)


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
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to list episodes: {e}")
        # In test, raise to avoid masking issues
        if get_settings().environment == "test":
            raise
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


# -----------------------------------------------------------------------------
# VoiceLive v2: Async Memory Enrichment Endpoint
# -----------------------------------------------------------------------------

class EnrichRequest(BaseModel):
    """Request body for voice transcript enrichment"""
    text: str
    session_id: Optional[str] = None
    speaker: str = "user"  # 'user' or 'assistant'
    agent_id: Optional[str] = None
    channel: str = "voice"


class EnrichResponse(BaseModel):
    """Response for enrichment request"""
    success: bool
    session_id: str
    message: str


@router.post("/enrich", response_model=EnrichResponse)
async def enrich_memory(request: EnrichRequest, user: SecurityContext = Depends(get_current_user)):
    """
    Enrich memory with voice transcripts or automation context.
    
    This endpoint is called by the browser after receiving transcription
    from the Azure Realtime API, or by automation tools to store context.
    It's fire-and-forget — the experience continues regardless of 
    whether memory persistence succeeds.
    """
    import logging
    import uuid
    from datetime import datetime, timezone
    from backend.memory.client import memory_client
    
    logger = logging.getLogger(__name__)
    
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"voice-{uuid.uuid4()}"
        
        # Create/update session with metadata including summary from content
        summary = request.text[:200] + ("..." if len(request.text) > 200 else "")
        
        await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user.user_id,
            metadata={
                "tenant_id": user.tenant_id,
                "channel": request.channel,
                "agent_id": request.agent_id or "unknown",
                "summary": summary,
                "turn_count": 1,
            },
        )
        
        # Directly add the message to memory (bypassing EnterpriseContext complexity)
        role = "user" if request.speaker == "user" else "assistant"
        await memory_client.add_memory(
            session_id=session_id,
            messages=[{
                "role": role,
                "content": request.text,
                "metadata": {
                    "agent_id": request.agent_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "channel": request.channel,
                },
            }],
        )
        
        logger.info(f"Memory enriched: session={session_id}, speaker={request.speaker}, len={len(request.text)}")
        
        return EnrichResponse(
            success=True,
            session_id=session_id,
            message="Transcript enriched successfully",
        )
        
    except Exception as e:
        logger.warning(f"Memory enrichment failed (non-blocking): {e}")
        return EnrichResponse(
            success=False,
            session_id=request.session_id or "",
            message=f"Enrichment failed: {str(e)}",
        )

