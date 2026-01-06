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


class MemoryEnvironment(BaseModel):
    name: str
    zep_api_url: str
    description: str


class MemoryEnvironmentsResponse(BaseModel):
    active_zep_api_url: str
    environments: list[MemoryEnvironment]


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


class GraphStatistics(BaseModel):
    total_nodes: int
    total_edges: int
    node_types: dict[str, int]
    avg_degree: float
    max_degree: int


class MemoryGraphResponse(BaseModel):
    nodes: list[GraphNodeView]
    edges: list[GraphEdgeView]
    stats: GraphStatistics | None = None


async def _build_graph(user_id: str, query: str) -> MemoryGraphResponse:
    from backend.memory.client import memory_client

    nodes: dict[str, GraphNodeView] = {}
    edges: list[GraphEdgeView] = []

    # Keep minimal in-memory indexes so we can add relationship types after
    # collecting nodes from facts + sessions.
    fact_metadata_by_id: dict[str, dict] = {}
    
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
            fact_metadata_by_id[fact.id] = getattr(fact, "metadata", {}) or {}
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
        # Get recent sessions (increase limit for better graph coverage)
        sessions = await memory_client.list_sessions(user_id=user_id, limit=50)
        
        for sess in sessions:
            sess_id = sess.get("session_id")
            meta = sess.get("metadata", {})
            summary = meta.get("summary", "Conversation")
            topics = meta.get("topics", [])
            agent_id = meta.get("agent_id")
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                if not (query_lower in summary.lower() or 
                        any(query_lower in topic.lower() for topic in topics)):
                    continue
            
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
                metadata={
                    "full_content": summary, 
                    "timestamp": sess.get("created_at"),
                    "agent_id": agent_id,
                    "turn_count": meta.get("turn_count", 0),
                    # Optional provenance fields if present
                    "tenant_id": meta.get("tenant_id"),
                    "channel": meta.get("channel"),
                    "source": meta.get("source"),
                    "filename": meta.get("filename"),
                },
            )

            # Link Episode to Agent (as an entity node) to enrich relationship traversal
            if agent_id:
                agent_node_id = f"entity-agent-{str(agent_id).lower().replace(' ', '-')}"
                ensure_node(
                    node_id=agent_node_id,
                    content=f"Agent: {agent_id}",
                    node_type="entity",
                    metadata={"kind": "agent"},
                )
                edges.append(
                    GraphEdgeView(
                        id=f"edge-{sess_id}-{agent_node_id}",
                        source=sess_id,
                        target=agent_node_id,
                        label="by",
                        weight=1.0,
                    )
                )
            
            # Create Topic Nodes and Edges
            for topic in topics:
                topic_id = f"topic-{topic.lower().replace(' ', '-')}"
                ensure_node(
                    node_id=topic_id,
                    content=topic,
                    node_type="topic",  # Use "topic" as a distinct type
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
                ensure_node(meta_id, f"{key}: {value_str}", "meta", {"source": key})
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

    # 4. Enrich with additional relationship types
    #    - Fact → Topic (about)
    #    - Fact → Agent (attributed_to)
    #    - Episode → Meta (provenance)

    def _normalize_id_fragment(value: str) -> str:
        return value.strip().lower().replace(" ", "-")

    # 4a. Fact → Topic / Agent
    for fact_id, meta in fact_metadata_by_id.items():
        if fact_id not in nodes:
            continue

        # Fact → Topic
        topics_value = meta.get("topics") or meta.get("topic")
        topics_list: list[str] = []
        if isinstance(topics_value, list):
            topics_list = [str(t) for t in topics_value if t is not None]
        elif isinstance(topics_value, str) and topics_value.strip():
            topics_list = [topics_value]

        for t in topics_list:
            topic_text = t.strip()
            if not topic_text:
                continue
            topic_id = f"topic-{_normalize_id_fragment(topic_text)}"
            ensure_node(topic_id, topic_text, "topic", {"kind": "topic"})
            edges.append(
                GraphEdgeView(
                    id=f"edge-{fact_id}-{topic_id}",
                    source=fact_id,
                    target=topic_id,
                    label="about",
                    weight=1.0,
                )
            )

        # Fact → Agent
        agent_value = meta.get("agent_id")
        if isinstance(agent_value, str) and agent_value.strip():
            agent_node_id = f"entity-agent-{_normalize_id_fragment(agent_value)}"
            ensure_node(agent_node_id, f"Agent: {agent_value}", "entity", {"kind": "agent"})
            edges.append(
                GraphEdgeView(
                    id=f"edge-{fact_id}-{agent_node_id}-attr",
                    source=fact_id,
                    target=agent_node_id,
                    label="attributed_to",
                    weight=1.0,
                )
            )

    # 4b. Episode → Meta (provenance)
    episode_meta_keys = {"tenant_id", "channel", "source", "filename"}
    for node in list(nodes.values()):
        if node.node_type != "memory":
            continue
        meta = node.metadata or {}
        for key in episode_meta_keys:
            raw_value = meta.get(key)
            if raw_value is None:
                continue
            value_str = str(raw_value)
            if not value_str.strip():
                continue
            meta_id = f"meta-{key}-{value_str}".replace(" ", "-")
            ensure_node(meta_id, f"{key}: {value_str}", "meta", {"source": key})
            edges.append(
                GraphEdgeView(
                    id=f"edge-{node.id}-{meta_id}-prov",
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

    # Calculate statistics
    node_list = list(nodes.values())
    node_types: dict[str, int] = {}
    total_degree = 0
    max_degree = 0
    
    for node in node_list:
        node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        total_degree += node.degree
        max_degree = max(max_degree, node.degree)
    
    stats = GraphStatistics(
        total_nodes=len(node_list),
        total_edges=len(edges),
        node_types=node_types,
        avg_degree=total_degree / len(node_list) if node_list else 0.0,
        max_degree=max_degree,
    )

    return MemoryGraphResponse(nodes=node_list, edges=edges, stats=stats)


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
    """
    Return a knowledge graph for the current user with statistics.
    
    This endpoint provides the Graph Knowledge (Gk) layer of Engram's tri-search capability:
    - Keyword Search: Full-text matching in session content
    - Vector Search: Semantic similarity via embeddings  
    - Graph Search: Relationship traversal (this endpoint)
    
    Results are combined using Reciprocal Rank Fusion (RRF) for optimal retrieval.
    
    Query parameter filters facts and episodes by content/topics.
    """
    try:
        return await _build_graph(user.user_id, query)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to build graph: {e}", exc_info=True)
        if get_settings().environment == "test":
            raise
        # Return empty graph with stats
        return MemoryGraphResponse(
            nodes=[], 
            edges=[],
            stats=GraphStatistics(
                total_nodes=0,
                total_edges=0,
                node_types={},
                avg_degree=0.0,
                max_degree=0,
            )
        )


@router.get("/environments", response_model=MemoryEnvironmentsResponse)
async def get_memory_environments(user: SecurityContext = Depends(get_current_user)):
    """Expose memory environment metadata for UI transparency."""
    import os
    from backend.memory.environments import list_environment_presets

    return MemoryEnvironmentsResponse(
        active_zep_api_url=os.getenv("ZEP_API_URL", ""),
        environments=[MemoryEnvironment(**e) for e in list_environment_presets()],
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
    user: SecurityContext = Depends(get_current_user),
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
            project_id=user.project_id,
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
    metadata: dict = {}


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
        
        # Merge request metadata with session metadata
        session_metadata = {
            "tenant_id": user.tenant_id,
            "channel": request.channel,
            "agent_id": request.agent_id or "unknown",
            "summary": summary,
            "turn_count": 1,
            **request.metadata  # Include extra context in session metadata too
        }

        await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user.user_id,
            metadata=session_metadata,
        )
        
        # Directly add the message to memory (bypassing EnterpriseContext complexity)
        role = "user" if request.speaker == "user" else "assistant"
        
        # Merge message metadata
        message_metadata = {
            "agent_id": request.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": request.channel,
            **request.metadata
        }

        await memory_client.add_memory(
            session_id=session_id,
            messages=[{
                "role": role,
                "content": request.text,
                "metadata": message_metadata,
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

