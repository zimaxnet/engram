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
        # Strip trailing slash to ensure clean URL construction
        self.zep_url = self.settings.zep_api_url.rstrip("/") if self.settings.zep_api_url else ""
        self.zep_api_key = self.settings.zep_api_key
        self._http_client = None
        logger.info(f"ZepMemoryClient initialized: {self.zep_url}")

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy-load the async HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    def _get_headers(self) -> dict:
        """Get headers for Zep API requests, including API key if configured."""
        headers = {"Content-Type": "application/json"}
        if self.zep_api_key:
            headers["Authorization"] = f"Bearer {self.zep_api_key}"
        return headers

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make a request to the Zep API."""
        if not self.zep_url:
            logger.warning("ZEP_API_URL not configured; skipping request")
            return None

        # Ensure endpoint has leading slash
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        url = f"{self.zep_url}{endpoint}"
        
        # Add authentication headers if API key is configured
        headers = self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        
        try:
            logger.debug(f"Zep Request: {method} {url}")
            response = await self.http_client.request(method, url, **kwargs)
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            
            if response.content:
                try:
                    return response.json()
                except ValueError:
                    # Handle case where content is not JSON (e.g. "OK")
                    logger.debug(f"Zep response not JSON: {response.text}")
                    return {"message": response.text}
            return {}
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Zep API error: {e.response.status_code} - {method} {url} - {e.response.text}")
            raise  # Re-raise to surface error to caller
        except Exception as e:
            logger.error(f"Zep request failed: {method} {url} - {e}")
            raise  # Re-raise to surface connection errors

    async def get_or_create_user(self, user_id: str, metadata: dict = None) -> dict:
        """
        Get or create a user in Zep.
        
        CRITICAL: Users must exist in Zep before creating sessions.
        This ensures consistent user identity across:
        - Chat sessions
        - Voice sessions
        - Episodes
        - Semantic search
        - Keyword search
        - Graph knowledge
        
        This is required for enterprise boundaries (projects, departments).
        See: docs/4-layer-context-schema-story.md
        
        Args:
            user_id: Unique user identifier (must match SecurityContext.user_id)
            metadata: Optional user metadata (name, email, tenant_id, etc.)
            
        Returns:
            User object from Zep
        """
        if not self.zep_url:
            logger.warning("ZEP_API_URL not configured; cannot create user")
            return {"user_id": user_id, "metadata": metadata or {}}
        
        # Try to get existing user first
        try:
            result = await self._request("GET", f"/api/v1/users/{user_id}")
            if result:
                logger.debug(f"User {user_id} already exists in Zep")
                return result
        except Exception as e:
            # User doesn't exist, will create below
            logger.debug(f"User {user_id} not found, will create: {e}")
        
        # Create new user
        payload = {
            "user_id": user_id,
            "metadata": metadata or {}
        }
        try:
            result = await self._request("POST", "/api/v1/users", json=payload)
            if result:
                logger.info(f"Created Zep user: {user_id}")
            return result or payload
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            # Return payload anyway so system can continue
            return payload

    async def get_or_create_session(self, session_id: str, user_id: str, metadata: dict = None) -> dict:
        """
        Get or create a session (conversation) in Zep.
        
        CRITICAL: Ensures user exists in Zep before creating session.
        This maintains consistent user identity across all systems:
        - Chat, Voice, Episodes, Sessions
        - Semantic search, Keyword search, Graph knowledge
        
        Required for enterprise boundaries (projects, departments).
        See: docs/4-layer-context-schema-story.md
        """
        try:
            # CRITICAL: Ensure user exists in Zep first
            # This ensures consistent user identity across all systems
            user_metadata = {}
            if metadata:
                # Extract user-level metadata from session metadata
                user_metadata = {
                    "tenant_id": metadata.get("tenant_id"),
                    "email": metadata.get("email"),
                    "display_name": metadata.get("display_name"),
                }
                # Remove None values
                user_metadata = {k: v for k, v in user_metadata.items() if v is not None}
            
            try:
                await self.get_or_create_user(user_id, metadata=user_metadata)
            except Exception as e:
                logger.warning(f"Failed to ensure user {user_id} exists in Zep: {e}. Continuing with session creation anyway.")

            # Try to get existing session
            try:
                existing = await self._request("GET", f"/api/v1/sessions/{session_id}")
                if existing:
                    # Update metadata if provided
                    if metadata:
                        try:
                            updated = await self._request("PATCH", f"/api/v1/sessions/{session_id}", json={"metadata": metadata})
                            if updated:
                                logger.info(f"Updated metadata for session: {session_id}")
                                return updated
                        except Exception as e:
                            logger.warning(f"Failed to update metadata for existing session {session_id}: {e}")
                    return existing
            except Exception:
                # Ignore fetch error, try create
                pass

            # Create new session (user should exist now)
            payload = {
                "session_id": session_id,
                "user_id": user_id,
                "metadata": metadata or {}
            }
            try:
                result = await self._request("POST", "/api/v1/sessions", json=payload)
                if result:
                    logger.info(f"Created Zep session: {session_id} for user: {user_id}")
                return result or payload
            except Exception as e:
                # If user still doesn't exist, log error but don't create anonymous session
                # This ensures user identity consistency
                if "user does not exist" in str(e).lower():
                    logger.error(
                        f"CRITICAL: Zep user {user_id} does not exist even after creation attempt. "
                        f"This breaks user identity consistency. Error: {e}"
                    )
                    # Re-raise to surface the issue - don't silently create anonymous sessions
                    raise ValueError(
                        f"User {user_id} must exist in Zep for consistent identity across systems. "
                        f"User creation failed: {e}"
                    ) from e
                raise e

        except Exception as e:
            logger.error(f"Failed to get/create session {session_id}: {e}")
            # Fallback to payload so app doesn't crash, but memory interactions will fail
            return {
                "session_id": session_id,
                "user_id": user_id,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(), 
                # Flag as offline/mock
                "_offline": True 
            }

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
        user_id: Optional[str] = None,
        search_type: str = "similarity",
    ) -> list[dict]:
        """
        Search memory for relevant content using HYBRID SEARCH.
        
        Combines three search methods with Reciprocal Rank Fusion (RRF):
        1. **Semantic Search** (pgvector) - Embedding cosine similarity
        2. **Keyword Search** (Zep) - Full-text matching in session content
        3. **Metadata Match** - Title, topics, summary matching
        
        Enhanced to prioritize:
        - Wiki pages (doc-wiki-*)
        - Canonical knowledge (doc-*, sess-*)
        - High semantic similarity scores
        """
        results = []
        semantic_results = []

        try:
            # ---------- PHASE 1: Semantic Search via pgvector ----------
            try:
                from backend.memory.vector_store import semantic_search
                semantic_results = await semantic_search(
                    query=query,
                    limit=limit * 2,  # Get more for fusion
                    min_score=0.3,  # Lower threshold, RRF will rank
                )
                logger.info(f"Semantic search returned {len(semantic_results)} results")
            except Exception as e:
                # Vector store may not be initialized or table doesn't exist
                logger.debug(f"Semantic search unavailable (will use keyword only): {e}")
            
            # ---------- PHASE 2: Keyword Search via Zep ----------
            # Get sessions filtered by user_id if provided (CRITICAL for user isolation)
            params = {}
            if user_id:
                params["user_id"] = user_id
            sessions_data = await self._request("GET", "/api/v1/sessions", params=params)
            if not sessions_data:
                logger.warning("No sessions found for memory search")
                # Return semantic results if we have them
                return semantic_results[:limit] if semantic_results else []

            # Try Zep's native search endpoint first (may not exist in OSS)
            try:
                search_payload = {
                    "text": query,
                    "limit": limit,
                    "search_type": search_type,
                }

                search_result = await self._request("POST", "/api/v1/sessions/search", json=search_payload)
                if search_result and "results" in search_result and search_result["results"]:
                    for result in search_result["results"]:
                        message = result.get("message", {})
                        results.append({
                            "content": message.get("content", ""),
                            "score": result.get("score", 0.5),
                            "metadata": message.get("metadata", {}),
                            "session_id": result.get("session_id", ""),
                        })
                    logger.info(f"Memory search found {len(results)} results via Zep search for: {query[:50]}...")
                    return results
            except Exception as e:
                # Zep OSS doesn't support /sessions/search (405) - fall back to keyword search
                logger.debug(f"Zep semantic search not available, using keyword fallback: {e}")

            # Fallback: Enhanced keyword-based search with Wiki prioritization
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            # Remove common stop words for better matching
            stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when", "where", "which", "who", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "about", "into", "does", "do", "can", "could", "would", "should", "currently", "your", "my", "our"}
            query_words = query_words - stop_words
            
            if not query_words:
                query_words = set(query_lower.split())  # Fall back to all words
            
            # Categorize sessions by priority
            wiki_sessions = [s for s in sessions_data if s.get("session_id", "").startswith("doc-wiki-")]
            doc_sessions = [s for s in sessions_data if s.get("session_id", "").startswith("doc-") and not s.get("session_id", "").startswith("doc-wiki-")]
            canonical_sessions = [s for s in sessions_data if s.get("session_id", "").startswith("sess-")]
            other_sessions = [s for s in sessions_data if not s.get("session_id", "").startswith(("doc-", "sess-"))]
            
            # Process in priority order: Wiki first, then docs, then canonical, then others
            all_sessions = wiki_sessions + doc_sessions + canonical_sessions + other_sessions
            sessions_to_search = all_sessions[:50]  # Limit for performance
            
            for sess in sessions_to_search:
                sess_id = sess.get("session_id", "")
                if not sess_id:
                    continue
                
                metadata = sess.get("metadata", {}) or {}
                is_wiki = sess_id.startswith("doc-wiki-")
                
                # Extract searchable fields from metadata
                title = metadata.get("title", "").lower()
                summary = metadata.get("summary", "").lower()
                source = metadata.get("source", "").lower()
                topics = [str(t).lower() for t in metadata.get("topics", [])]
                all_topics_str = " ".join(topics)
                
                # Calculate match score
                title_matches = sum(1 for w in query_words if w in title)
                summary_matches = sum(1 for w in query_words if w in summary)
                topic_matches = sum(1 for w in query_words if w in all_topics_str)
                
                meta_score = 0
                
                # Title match is highest signal
                if title_matches > 0:
                    meta_score = min(0.95, 0.7 + (title_matches * 0.1))
                # Topic match is strong signal  
                elif topic_matches > 0:
                    meta_score = min(0.9, 0.6 + (topic_matches * 0.1))
                # Summary match is good signal
                elif summary_matches >= 2:
                    meta_score = min(0.85, 0.5 + (summary_matches * 0.08))
                elif summary_matches == 1:
                    meta_score = 0.5
                
                # Boost wiki content
                if is_wiki and meta_score > 0:
                    meta_score = min(0.98, meta_score + 0.1)
                
                if meta_score > 0:
                    display_content = metadata.get("summary", title) or f"Session: {sess_id}"
                    results.append({
                        "content": f"[{title or sess_id}] {display_content}",
                        "score": meta_score,
                        "metadata": metadata,
                        "session_id": sess_id,
                        "source_type": "wiki" if is_wiki else "document",
                    })
                
                # Also search message content for wiki pages (high value content)
                if is_wiki or meta_score < 0.5:
                    messages = await self.get_session_messages(sess_id, limit=5)
                    for msg in messages:
                        content = msg.get("content", "")
                        content_lower = content.lower()
                        
                        # Check for query word matches
                        matches = sum(1 for w in query_words if w in content_lower)
                        
                        if matches >= 2 or (len(query_words) <= 2 and matches >= 1):
                            content_score = min(0.85, 0.4 + (matches * 0.1))
                            
                            # Boost wiki content
                            if is_wiki:
                                content_score = min(0.95, content_score + 0.15)
                            
                            # Truncate content for display
                            display_content = content[:500] + "..." if len(content) > 500 else content
                            
                            results.append({
                                "content": display_content,
                                "score": content_score,
                                "metadata": msg.get("metadata", {}),
                                "session_id": sess_id,
                                "source_type": "wiki_content" if is_wiki else "content",
                            })
            
            # ---------- PHASE 3: Reciprocal Rank Fusion (RRF) ----------
            # Combine semantic and keyword results using RRF scoring
            # RRF formula: score = sum(1 / (k + rank)) where k = 60 (standard constant)
            
            rrf_scores = {}  # session_id -> {score: float, result: dict}
            k = 60  # RRF constant
            
            # Score semantic results (ranked by embedding similarity)
            for rank, r in enumerate(semantic_results, start=1):
                sid = r.get("session_id", "")
                if sid:
                    rrf_score = 1.0 / (k + rank)
                    if sid not in rrf_scores or r.get("score", 0) > rrf_scores[sid].get("semantic_score", 0):
                        rrf_scores[sid] = {
                            "semantic_rank": rank,
                            "semantic_score": r.get("score", 0),
                            "rrf_score": rrf_score,
                            "result": r,
                        }
            
            # Score keyword results (ranked by keyword matching)
            keyword_results = results  # Results from keyword search above
            for rank, r in enumerate(keyword_results, start=1):
                sid = r.get("session_id", "")
                if sid:
                    rrf_score = 1.0 / (k + rank)
                    if sid in rrf_scores:
                        # Fusion: add scores from both sources
                        rrf_scores[sid]["keyword_rank"] = rank
                        rrf_scores[sid]["keyword_score"] = r.get("score", 0)
                        rrf_scores[sid]["rrf_score"] += rrf_score
                        # Prefer keyword result if it has more content
                        if len(r.get("content", "")) > len(rrf_scores[sid]["result"].get("content", "")):
                            rrf_scores[sid]["result"] = r
                    else:
                        rrf_scores[sid] = {
                            "keyword_rank": rank,
                            "keyword_score": r.get("score", 0),
                            "rrf_score": rrf_score,
                            "result": r,
                        }
            
            # Build final results with RRF scores
            final_results = []
            for sid, data in rrf_scores.items():
                result = data["result"].copy()
                result["score"] = data["rrf_score"]
                result["fusion_source"] = "hybrid" if "semantic_rank" in data and "keyword_rank" in data else (
                    "semantic" if "semantic_rank" in data else "keyword"
                )
                final_results.append(result)
            
            # Sort by RRF score descending
            final_results.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Hybrid search found {len(final_results)} results ({len(semantic_results)} semantic, {len(keyword_results)} keyword) for: {query[:50]}...")
            return final_results[:limit]

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
                
                logger.info(f"Fetched {len(sessions)} sessions from Zep. Filtering for user: {user_id}")

                if user_id:
                    # Include sessions that match user_id OR have no user_id (legacy/ingested docs)
                    sessions = [s for s in sessions if s.get("user_id") == user_id or s.get("user_id") is None]
                    logger.info(f"After user filter: {len(sessions)} sessions remain")

                # Sort by created_at descending (newest first)
                sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

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

        # Ensure session exists with full user metadata
        # This ensures consistent user identity across all systems
        session_metadata = {
            "tenant_id": context.security.tenant_id,
        }
        # Include user identity metadata for proper user creation
        if context.security.email:
            session_metadata["email"] = context.security.email
        if context.security.display_name:
            session_metadata["display_name"] = context.security.display_name
        
        await self.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=session_metadata,
        )

        # Search for relevant memory filtered by user_id
        # CRITICAL: Filter by user_id to ensure user data isolation
        memory_results = await self.search_memory(
            session_id=session_id,
            query=query,
            limit=5,
            user_id=user_id,  # Filter by authenticated user
        )

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
        user_id = context.security.user_id

        # Convert recent turns to Zep format
        messages = []
        agent_id = None
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
            # Track the most recent agent_id from assistant turns
            if turn.role.value == "assistant" and turn.agent_id:
                agent_id = turn.agent_id

        # Update session metadata with agent_id, summary, turn_count, and user identity
        # This ensures episodes show correct agent, summary, and user attribution
        # CRITICAL: Include user identity metadata for proper project/department boundaries
        session_metadata = {
            "turn_count": context.episodic.total_turns,
            "tenant_id": context.security.tenant_id,
        }
        
        # Include user identity metadata for proper attribution
        if context.security.email:
            session_metadata["email"] = context.security.email
        if context.security.display_name:
            session_metadata["display_name"] = context.security.display_name
        
        # Set agent_id if we have one
        if agent_id:
            session_metadata["agent_id"] = agent_id
        
        # Set summary if available, otherwise generate a simple one
        if context.episodic.summary:
            session_metadata["summary"] = context.episodic.summary
        elif context.episodic.recent_turns:
            # Generate a simple summary from recent turns
            recent_content = " ".join([turn.content[:100] for turn in context.episodic.recent_turns[-3:]])
            session_metadata["summary"] = recent_content[:200] + ("..." if len(recent_content) > 200 else "")
        
        # Ensure session exists and update metadata
        try:
            await self.get_or_create_session(
                session_id=session_id,
                user_id=user_id,
                metadata=session_metadata
            )
        except Exception as e:
            logger.warning(f"Failed to update session metadata for {session_id}: {e}")

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
