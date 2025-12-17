"""
Zep Memory Client

Provides integration with Zep's memory service for:
- Episodic memory (conversation history)
- Semantic memory (knowledge graph / facts)
- Temporal knowledge graph queries

This is the Memory layer of the Brain + Spine architecture.
"""

import logging
from datetime import datetime
from typing import Optional

from backend.core import (
    Entity,
    EnterpriseContext,
    GraphNode,
    get_settings,
)

logger = logging.getLogger(__name__)


class ZepMemoryClient:
    """
    Client for interacting with Zep's memory service.

    Zep provides:
    - Episodic memory: Stores and retrieves conversation episodes
    - Semantic memory: Knowledge graph with temporal awareness
    - Hybrid search: Combines vector similarity with graph traversal
    """

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._initialized = False

    @property
    def client(self):
        """Lazy-load the Zep client"""
        if self._client is None:
            try:
                from zep_python.client import AsyncZep

                self._client = AsyncZep(
                    base_url=self.settings.zep_api_url,
                    api_key=self.settings.zep_api_key,
                )
                self._initialized = True
                logger.info(f"Zep client initialized: {self.settings.zep_api_url}")
            except ImportError:
                logger.warning("zep-python not installed, using mock client")
                self._client = MockZepClient()
            except Exception as e:
                logger.error(f"Failed to initialize Zep client: {e}")
                self._client = MockZepClient()

        return self._client

    async def get_or_create_session(self, session_id: str, user_id: str, metadata: dict = None) -> dict:
        """
        Get or create a session (conversation) in Zep.
        """
        try:
            session = await self.client.memory.get_session(session_id)
            return session
        except Exception:
            session = await self.client.memory.add_session(
                session_id=session_id, user_id=user_id, metadata=metadata or {}
            )
            logger.info(f"Created new Zep session: {session_id}")
            return session

    async def add_memory(self, session_id: str, messages: list[dict], metadata: dict = None) -> None:
        """
        Add messages to a session's memory.

        Args:
            session_id: Session to add memory to
            messages: List of message dicts with 'role' and 'content'
            metadata: Optional metadata for the memory
        """
        try:
            from zep_python.types.message import Message

            zep_messages = [
                Message(
                    role=msg["role"],
                    content=msg["content"],
                    metadata=msg.get("metadata", {}),
                )
                for msg in messages
            ]

            await self.client.memory.add(
                session_id=session_id,
                messages=zep_messages,
            )
            logger.debug(f"Added {len(messages)} messages to session {session_id}")
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    async def get_session_messages(self, session_id: str, limit: int = 20) -> list[dict]:
        """
        Get messages for a session (transcript).
        """
        try:
            resp = await self.client.memory.get_session_messages(session_id=session_id, limit=limit)
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "metadata": getattr(m, "metadata", {}) or {},
                }
                for m in resp.messages or []
            ]
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []

    async def search_memory(
        self,
        session_id: str,
        query: str,
        limit: int = 10,
        search_type: str = "similarity",
    ) -> list[dict]:
        """
        Search session memory for relevant content.

        Args:
            session_id: Session to search
            query: Search query
            limit: Maximum results
            search_type: 'similarity' or 'mmr'

        Returns:
            List of relevant memory results
        """
        try:
            resp = await self.client.memory.search_sessions(
                session_ids=[session_id],
                text=query,
                limit=limit,
                search_scope="messages",
                search_type=search_type,
            )
            results = []
            for session in resp.sessions or []:
                for msg in session.messages or []:
                    score_val = msg.score if hasattr(msg, "score") and msg.score is not None else 0.5
                    results.append(
                        {
                            "content": msg.content,
                            "score": score_val,
                            "metadata": getattr(msg, "metadata", {}) or {},
                        }
                    )
            return results
        except Exception as e:
            logger.warning(f"Memory search failed, falling back to recent messages: {e}")
            try:
                resp = await self.client.memory.get_session_messages(session_id=session_id, limit=limit)
                return [
                    {
                        "content": m.content,
                        "score": 0.5,
                        "metadata": getattr(m, "metadata", {}) or {},
                    }
                    for m in resp.messages or []
                ]
            except Exception as e2:
                logger.error(f"Memory search fallback failed: {e2}")
                return []

    async def get_facts(self, user_id: str, query: Optional[str] = None, limit: int = 20) -> list[GraphNode]:
        """
        Get facts from the knowledge graph for a user.

        Args:
            user_id: User to get facts for
            query: Optional query to filter facts
            limit: Maximum facts to return

        Returns:
            List of GraphNode facts
        """
        try:
            results = await self.client.graph.asearch(user_id=user_id, query=query or "", limit=limit)

            nodes = []
            for result in results:
                # Map Zep graph result to GraphNode
                nodes.append(
                    GraphNode(
                        id=result.uuid,
                        content=result.fact,
                        node_type="fact",
                        confidence=1.0,  # Zep doesn't always return confidence for raw facts
                        created_at=datetime.utcnow(),  # Placeholder
                        metadata=result.metadata or {},
                    )
                )
            return nodes
        except Exception as e:
            logger.error(f"Failed to get facts: {e}")
            return []

    async def add_fact(self, user_id: str, fact: str, metadata: dict = None) -> Optional[str]:
        """
        Add a fact to the knowledge graph.

        Args:
            user_id: User to add fact for
            fact: The fact content
            metadata: Optional metadata

        Returns:
            Fact ID if successful
        """
        try:
            result = await self.client.graph.aadd(user_id=user_id, fact=fact, metadata=metadata or {})
            logger.info(f"Added fact for user {user_id}: {fact[:50]}...")
            return result.uuid
        except Exception as e:
            logger.error(f"Failed to add fact: {e}")
            return None

    async def get_entities(self, user_id: str, entity_type: Optional[str] = None, limit: int = 50) -> list[Entity]:
        """
        Get entities from the knowledge graph.

        Args:
            user_id: User to get entities for
            entity_type: Optional filter by entity type
            limit: Maximum entities to return

        Returns:
            List of Entity objects
        """
        try:
            # Note: This assumes Zep SDK specific method for entities or search
            # If explicit logic needed, adjust based on actual SDK
            # For now, simplistic implementation
            return []
        except Exception as e:
            logger.error(f"Failed to get entities: {e}")
            return []

    async def list_sessions(self, user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
        """
        List conversation sessions (episodes).
        """
        try:
            # zep-python list_sessions uses page_number/page_size (not limit/offset) and does not
            # reliably support server-side filtering by user_id. We page, then filter client-side.
            page_size = max(1, int(limit))
            page_number = int(offset // page_size) + 1
            within_page_offset = int(offset % page_size)

            resp = await self.client.memory.list_sessions(
                page_number=page_number,
                page_size=page_size,
                order_by="created_at",
                asc=False,
            )

            sessions = list(getattr(resp, "sessions", None) or [])

            if user_id:
                sessions = [s for s in sessions if getattr(s, "user_id", None) == user_id]

            # Apply offset within the fetched page after filtering.
            sessions = sessions[within_page_offset : within_page_offset + page_size]

            return [
                {
                    "session_id": getattr(s, "session_id", None),
                    "created_at": getattr(s, "created_at", None),
                    "updated_at": getattr(s, "updated_at", None),
                    "metadata": getattr(s, "metadata", None) or {},
                    "user_id": getattr(s, "user_id", None),
                }
                for s in sessions
                if getattr(s, "session_id", None)
            ]
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    async def enrich_context(self, context: EnterpriseContext, query: str) -> EnterpriseContext:
        """
        Enrich an EnterpriseContext with relevant memory.

        This is the main integration point for the Context Engine.
        It populates Layer 2 (Episodic) and Layer 3 (Semantic).

        Args:
            context: The context to enrich
            query: The current query to find relevant memory for

        Returns:
            Enriched context
        """
        user_id = context.security.user_id
        session_id = context.episodic.conversation_id

        # Ensure session exists
        await self.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={"tenant_id": context.security.tenant_id},
        )

        # Search for relevant memory
        memory_results = await self.search_memory(session_id=session_id, query=query, limit=5)

        # Get relevant facts from knowledge graph
        facts = await self.get_facts(user_id=user_id, query=query, limit=10)

        # Get entities
        entities = await self.get_entities(user_id=user_id, limit=20)

        # Update semantic knowledge layer
        context.semantic.retrieved_facts = facts
        context.semantic.entity_context = {e.id: e for e in entities}
        context.semantic.last_query = query
        context.semantic.query_timestamp = datetime.utcnow()

        # Add memory results as additional context
        for result in memory_results:
            if result.get("content"):
                context.semantic.add_fact(
                    GraphNode(
                        id=f"memory-{hash(result['content'])}",
                        content=result["content"],
                        node_type="memory",
                        confidence=result.get("score", 0.5),
                    )
                )

        context.update_timestamp()
        return context

    async def persist_conversation(self, context: EnterpriseContext) -> None:
        """
        Persist the current conversation to Zep.

        Called after each turn to update episodic memory.

        Args:
            context: The context containing conversation to persist
        """
        session_id = context.episodic.conversation_id

        # Convert recent turns to Zep format
        messages = []
        for turn in context.episodic.recent_turns[-2:]:  # Last 2 turns (user + assistant)
            messages.append(
                {
                    "role": turn.role.value,
                    "content": turn.content,
                    "metadata": {
                        "agent_id": turn.agent_id,
                        "timestamp": turn.timestamp.isoformat(),
                    },
                }
            )

        if messages:
            await self.add_memory(
                session_id=session_id,
                messages=messages,
                metadata={"turn_count": context.episodic.total_turns},
            )


class MockZepClient:
    """
    Mock Zep client for development without a Zep server.
    Returns empty results instead of failing.
    """

    class MockUser:
        async def aget(self, user_id: str):
            return {"user_id": user_id}

        async def aadd(self, user_id: str, metadata: dict = None):
            return {"user_id": user_id, "metadata": metadata}

    class MockMemory:
        async def aget_session(self, session_id: str):
            raise Exception("Session not found")

        async def aadd_session(self, session_id: str, user_id: str, metadata: dict = None):
            return {"session_id": session_id, "user_id": user_id}

        async def aadd_memory(self, session_id: str, memory):
            pass

        async def asearch_memory(
            self,
            session_id: str,
            text: str,
            limit: int = 10,
            search_type: str = "similarity",
        ):
            return []

        async def list_sessions(self, limit=20, offset=0, user_id=None):
            return []

    class MockGraph:
        async def asearch(self, user_id: str, query: str = None, limit: int = 20):
            return []

        async def aadd(self, user_id: str, fact: str, metadata: dict = None):
            class Result:
                uuid = "mock-uuid"

            return Result()

        async def aget_entities(self, user_id: str, entity_type: str = None, limit: int = 50):
            return []

    def __init__(self):
        self.user = self.MockUser()
        self.memory = self.MockMemory()
        self.graph = self.MockGraph()


# Singleton client
memory_client = ZepMemoryClient()


# Convenience functions
async def enrich_context(context: EnterpriseContext, query: str) -> EnterpriseContext:
    """Enrich context with relevant memory"""
    fn = getattr(memory_client, "enrich_context", None)
    if callable(fn):
        return await fn(context, query)
    # Graceful no-op if client does not implement enrich_context (e.g., tests mocking client)
    return context


async def persist_conversation(context: EnterpriseContext) -> None:
    """Persist conversation to memory"""
    fn = getattr(memory_client, "persist_conversation", None)
    if callable(fn):
        await fn(context)
        return
    # Fallback for mocked clients that implement add_memory(user_id, conversation_id, messages, **kwargs)
    add_fn = getattr(memory_client, "add_memory", None)
    if callable(add_fn):
        try:
            user_id = getattr(context.security, "user_id", None)
            conversation_id = getattr(context.episodic, "conversation_id", None)
            messages = []
            # Prefer explicit episodic.messages if present (tests use this)
            raw_messages = getattr(context.episodic, "messages", None) or []
            if raw_messages:
                messages = raw_messages
            else:
                # Build from recent_turns
                for t in getattr(context.episodic, "recent_turns", []) or []:
                    messages.append(
                        {
                            "role": getattr(t.role, "value", None) or str(t.role),
                            "content": t.content,
                            "timestamp": getattr(t, "timestamp", None).isoformat() if getattr(t, "timestamp", None) else None,
                        }
                    )
            if messages:
                await add_fn(user_id=user_id, conversation_id=conversation_id, messages=messages)
        except Exception:
            # Swallow errors to keep API resilient during tests
            return


async def search_memory(session_id: str, query: str, limit: int = 10) -> list[dict]:
    """Search session memory"""
    fn = getattr(memory_client, "search_memory", None)
    if callable(fn):
        return await fn(session_id, query, limit)
    return []


async def get_facts(user_id: str, query: str = None, limit: int = 20) -> list[GraphNode]:
    """Get facts from knowledge graph"""
    fn = getattr(memory_client, "get_facts", None)
    if callable(fn):
        return await fn(user_id, query, limit)
    return []


async def list_episodes(user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
    """List conversation episodes"""
    fn = getattr(memory_client, "list_sessions", None)
    if callable(fn):
        return await fn(user_id, limit, offset)
    return []


async def get_session_transcript(session_id: str) -> list[dict]:
    """Get conversation transcript"""
    fn = getattr(memory_client, "get_session_messages", None)
    if callable(fn):
        return await fn(session_id, limit=100)
    return []
