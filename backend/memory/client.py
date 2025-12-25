"""
Zep Memory Client - Production REST API

Provides direct REST API integration with Zep's memory service for:
- Episodic memory (conversation history)
- Semantic memory (knowledge graph / facts)
- Session search

This is the Memory layer of the Brain + Spine architecture.
NO MOCKS - Production staging environment only.
"""

import logging
from datetime import datetime
from typing import Optional
import httpx

from backend.core import (
    Entity,
    EnterpriseContext,
    GraphNode,
    get_settings,
)

logger = logging.getLogger(__name__)


class ZepMemoryClient:
    """
    Client for interacting with Zep's memory service via direct REST API.

    Production-only implementation - no mock fallbacks.
    Uses httpx for direct HTTP calls to Zep REST API.
    """

    def __init__(self):
        self.settings = get_settings()
        self.zep_url = self.settings.zep_api_url
        self._http_client = None
        logger.info(f"ZepMemoryClient initialized: {self.zep_url}")

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy-load the async HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make a request to the Zep API."""
        url = f"{self.zep_url}{endpoint}"
        try:
            response = await self.http_client.request(method, url, **kwargs)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            if response.content:
                return response.json()
            return {}
        except httpx.HTTPStatusError as e:
            logger.warning(f"Zep API error: {e.response.status_code} - {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Zep request failed: {e}")
            return None

    async def get_or_create_session(self, session_id: str, user_id: str, metadata: dict = None) -> dict:
        """
        Get or create a session (conversation) in Zep.
        """
        # Try to get existing session
        existing = await self._request("GET", f"/api/v1/sessions/{session_id}")
        if existing:
            return existing

        # Create new session
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        result = await self._request("POST", "/api/v1/sessions", json=payload)
        if result:
            logger.info(f"Created Zep session: {session_id}")
        return result or payload

    async def add_memory(self, session_id: str, messages: list[dict], metadata: dict = None) -> None:
        """
        Add messages to a session's memory.

        Args:
            session_id: Session to add memory to
            messages: List of message dicts with 'role' and 'content'
            metadata: Optional metadata for the memory
        """
        try:
            # Format messages for Zep API
            formatted_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                # Zep uses role_type instead of role
                formatted_messages.append({
                    "role_type": role if role in ["user", "assistant", "system"] else "user",
                    "content": msg["content"],
                    "metadata": msg.get("metadata", {})
                })

            payload = {"messages": formatted_messages}
            result = await self._request("POST", f"/api/v1/sessions/{session_id}/memory", json=payload)
            if result is not None:
                logger.debug(f"Added {len(messages)} messages to session {session_id}")
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    async def get_session_messages(self, session_id: str, limit: int = 20) -> list[dict]:
        """
        Get messages for a session (transcript).
        """
        try:
            result = await self._request("GET", f"/api/v1/sessions/{session_id}/messages", params={"limit": limit})
            if result and "messages" in result:
                return [
                    {
                        "role": m.get("role_type", m.get("role", "user")),
                        "content": m.get("content", ""),
                        "metadata": m.get("metadata", {}),
                    }
                    for m in result["messages"]
                ]
            return []
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
        Search memory for relevant content GLOBALLY across all sessions.

        This enables agents to access canonical episodic memories (like the vision
        statement in sess-vision-001) regardless of the current conversation session.
        """
        results = []

        try:
            # First, get all sessions to search globally
            sessions_data = await self._request("GET", "/api/v1/sessions")
            if sessions_data:
                all_session_ids = [s.get("session_id") for s in sessions_data if s.get("session_id")]

                # Include current session if not in list
                if session_id not in all_session_ids:
                    all_session_ids.append(session_id)

            # Search across sessions using Zep's search endpoint
            search_payload = {
                "text": query,
                "limit": limit,
                "search_type": search_type,
            }

            search_result = await self._request("POST", "/api/v1/sessions/search", json=search_payload)
            if search_result and "results" in search_result:
                for result in search_result["results"]:
                    message = result.get("message", {})
                    results.append({
                        "content": message.get("content", ""),
                        "score": result.get("score", 0.5),
                        "metadata": message.get("metadata", {}),
                        "session_id": result.get("session_id", ""),
                    })
                logger.info(f"Memory search found {len(results)} results for: {query[:50]}...")
                return results

            # Fallback: search individual sessions with word-based matching
            query_words = set(query.lower().split())
            if sessions_data:
                # Prioritize sessions that look like canonical knowledge (sess-* or doc-*)
                prioritized_sessions = [s for s in sessions_data if s.get("session_id", "").startswith(("sess-", "doc-"))]
                other_sessions = [s for s in sessions_data if not s.get("session_id", "").startswith(("sess-", "doc-"))]
                
                # Search up to 100 sessions, prioritizing canonical ones
                sessions_to_search = (prioritized_sessions + other_sessions)[:100]
                
                for sess in sessions_to_search:
                    sess_id = sess.get("session_id")
                    if not sess_id:
                        continue
                        
                    # 1. Match against session metadata (High relevance)
                    metadata = sess.get("metadata", {}) or {}
                    summary = metadata.get("summary", "").lower()
                    topics = [str(t).lower() for t in metadata.get("topics", [])]
                    
                    meta_matches = sum(1 for w in query_words if w in summary or any(w in t for t in topics))
                    if meta_matches >= 1:
                        results.append({
                            "content": f"[Session Summary: {metadata.get('summary', '')}]",
                            "score": min(0.95, 0.6 + (meta_matches * 0.15)),
                            "metadata": metadata,
                            "session_id": sess_id,
                        })

                    # 2. Match against messages
                    messages = await self.get_session_messages(sess_id, limit=20)
                    for msg in messages:
                        content = msg.get("content", "")
                        content_lower = content.lower()
                        # Score based on how many query words appear
                        matches = sum(1 for w in query_words if w in content_lower)
                        if matches >= 2 or (len(query_words) == 1 and matches == 1):
                            score = min(0.9, 0.5 + (matches * 0.1))
                            results.append({
                                "content": content,
                                "score": score,
                                "metadata": msg.get("metadata", {}),
                                "session_id": sess_id,
                            })
            
            # Sort by score descending
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []

    async def get_facts(self, user_id: str, query: Optional[str] = None, limit: int = 20) -> list[GraphNode]:
        """
        Get facts from the knowledge graph for a user.
        """
        try:
            params = {"limit": limit}
            if query:
                params["query"] = query

            result = await self._request("GET", f"/api/v1/users/{user_id}/facts", params=params)
            if result and isinstance(result, list):
                return [
                    GraphNode(
                        id=f.get("uuid", ""),
                        content=f.get("fact", ""),
                        node_type="fact",
                        confidence=1.0,
                        created_at=datetime.utcnow(),
                        metadata=f.get("metadata", {}),
                    )
                    for f in result
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to get facts: {e}")
            return []

    async def add_fact(self, user_id: str, fact: str, metadata: dict = None) -> Optional[str]:
        """
        Add a fact to the knowledge graph.
        """
        try:
            payload = {
                "fact": fact,
                "metadata": metadata or {}
            }
            result = await self._request("POST", f"/api/v1/users/{user_id}/facts", json=payload)
            if result:
                logger.info(f"Added fact for user {user_id}: {fact[:50]}...")
                return result.get("uuid")
            return None
        except Exception as e:
            logger.error(f"Failed to add fact: {e}")
            return None

    async def get_entities(self, user_id: str, entity_type: Optional[str] = None, limit: int = 50) -> list[Entity]:
        """
        Get entities from the knowledge graph.
        """
        # Zep's entity extraction is automatic - return empty for now
        return []

    # =============================================================================
    # Alias Methods for Story Activities Compatibility
    # =============================================================================

    async def add_session(
        self, session_id: str, user_id: str, metadata: dict = None
    ) -> dict:
        """
        Add/create a new session. Alias for get_or_create_session().
        
        Used by story_activities.py for memory enrichment.
        """
        return await self.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )

    async def add_messages(
        self, session_id: str, messages: list[dict]
    ) -> None:
        """
        Add messages to a session. Alias for add_memory().
        
        Used by story_activities.py for memory enrichment.
        """
        await self.add_memory(
            session_id=session_id,
            messages=messages,
        )

    async def list_sessions(self, user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
        """
        List conversation sessions (episodes).
        """
        try:
            result = await self._request("GET", "/api/v1/sessions")
            if result and isinstance(result, list):
                sessions = result

                if user_id:
                    sessions = [s for s in sessions if s.get("user_id") == user_id]

                # Apply pagination
                sessions = sessions[offset:offset + limit]

                return [
                    {
                        "session_id": s.get("session_id"),
                        "created_at": s.get("created_at"),
                        "updated_at": s.get("updated_at"),
                        "metadata": s.get("metadata") or {},
                        "user_id": s.get("user_id"),
                    }
                    for s in sessions
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    async def enrich_context(self, context: EnterpriseContext, query: str) -> EnterpriseContext:
        """
        Enrich an EnterpriseContext with relevant memory.

        This is the main integration point for the Context Engine.
        It populates Layer 2 (Episodic) and Layer 3 (Semantic).
        """
        user_id = context.security.user_id
        session_id = context.episodic.conversation_id

        # Ensure session exists
        await self.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={"tenant_id": context.security.tenant_id},
        )

        # Search for relevant memory across ALL sessions
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


# Singleton client
memory_client = ZepMemoryClient()


# Convenience functions
async def enrich_context(context: EnterpriseContext, query: str) -> EnterpriseContext:
    """Enrich context with relevant memory"""
    return await memory_client.enrich_context(context, query)


async def persist_conversation(context: EnterpriseContext) -> None:
    """Persist conversation to memory"""
    await memory_client.persist_conversation(context)


async def search_memory(session_id: str, query: str, limit: int = 10) -> list[dict]:
    """Search session memory"""
    return await memory_client.search_memory(session_id, query, limit)


async def get_facts(user_id: str, query: str = None, limit: int = 20) -> list[GraphNode]:
    """Get facts from knowledge graph"""
    return await memory_client.get_facts(user_id, query, limit)


async def list_episodes(user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> list[dict]:
    """List conversation episodes"""
    return await memory_client.list_sessions(user_id, limit, offset)


async def get_session_transcript(session_id: str) -> list[dict]:
    """Get conversation transcript"""
    return await memory_client.get_session_messages(session_id, limit=100)
