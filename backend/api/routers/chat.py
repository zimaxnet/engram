"""
Chat endpoints

Provides:
- REST endpoint for single-turn chat
- WebSocket endpoint for streaming chat
- Integration with LangGraph agents and Zep memory
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from backend.agents import chat as agent_chat, get_agent
from backend.agents.foundry_client import get_foundry_client
from backend.api.middleware.auth import get_current_user
from backend.core import EnterpriseContext, SecurityContext, MessageRole, Turn, get_settings
from backend.memory import enrich_context, persist_conversation

# Timeout for memory operations (seconds) - prevents blocking on slow/unreachable Zep
MEMORY_TIMEOUT = 2.0

logger = logging.getLogger(__name__)

router = APIRouter()


# Session storage (in production, use Redis or similar)
# Key format: {user_id}:{agent_id}:{project_id?}:{session_id}
# When USE_FOUNDRY_THREADS is enabled, Foundry threads are used for persistence
# but we still maintain in-memory cache for performance
_sessions: dict[str, EnterpriseContext] = {}
# Map session keys to Foundry thread IDs
_foundry_thread_map: dict[str, str] = {}


def _make_session_key(user_id: str, agent_id: str, session_id: str, project_id: Optional[str] = None) -> str:
    """
    Create a composite session key that ensures agent and user isolation.
    
    Format: {user_id}:{agent_id}:{project_id?}:{session_id}
    - user_id: Ensures user isolation
    - agent_id: Ensures each agent has separate conversation threads
    - project_id: Optional, enables project-based access when specified
    - session_id: The actual session identifier
    """
    parts = [user_id, agent_id]
    if project_id:
        parts.append(project_id)
    parts.append(session_id)
    return ":".join(parts)


async def _load_context_from_foundry_thread(
    thread_id: str,
    security: SecurityContext,
    agent_id: str,
    session_id: str
) -> Optional[EnterpriseContext]:
    """
    Load EnterpriseContext from Foundry thread messages.
    
    Returns None if Foundry is unavailable or thread doesn't exist.
    """
    foundry_client = get_foundry_client()
    if not foundry_client:
        return None
    
    try:
        # Get thread messages
        messages = await foundry_client.list_messages(thread_id, limit=100)
        
        # Create context from messages
        context = EnterpriseContext(security=security)
        context.episodic.conversation_id = session_id
        context.episodic.metadata = {
            "agent_id": agent_id,
            "project_id": security.project_id,
            "foundry_thread_id": thread_id,
        }
        
        # Convert Foundry messages to Turns
        for msg in reversed(messages):  # Reverse to get chronological order
            role_str = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Map Foundry roles to MessageRole
            if role_str == "user":
                role = MessageRole.USER
            elif role_str == "assistant":
                role = MessageRole.ASSISTANT
            else:
                role = MessageRole.SYSTEM
            
            # Extract timestamp from metadata or use current time
            metadata = msg.get("metadata", {})
            timestamp_str = metadata.get("timestamp")
            if timestamp_str:
                from datetime import datetime
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            turn = Turn(
                role=role,
                content=content,
                timestamp=timestamp,
                agent_id=agent_id if role == MessageRole.ASSISTANT else None,
            )
            context.episodic.add_turn(turn)
        
        logger.info(f"Loaded context from Foundry thread {thread_id}: {len(messages)} messages")
        return context
        
    except Exception as e:
        logger.warning(f"Failed to load context from Foundry thread {thread_id}: {e}")
        return None


async def _save_context_to_foundry_thread(
    thread_id: str,
    context: EnterpriseContext,
    agent_id: str
) -> bool:
    """
    Save EnterpriseContext turns to Foundry thread.
    
    Only saves new messages (not already persisted).
    Returns True if successful, False otherwise.
    """
    foundry_client = get_foundry_client()
    if not foundry_client:
        return False
    
    try:
        # Get existing messages to avoid duplicates
        existing_messages = await foundry_client.list_messages(thread_id, limit=100)
        existing_contents = {msg.get("content", "") for msg in existing_messages}
        
        # Save new turns
        saved_count = 0
        for turn in context.episodic.recent_turns:
            # Skip if message already exists
            if turn.content in existing_contents:
                continue
            
            role = "user" if turn.role == MessageRole.USER else "assistant"
            metadata = {
                "timestamp": turn.timestamp.isoformat(),
                "agent_id": turn.agent_id or agent_id,
            }
            
            await foundry_client.add_message(
                thread_id=thread_id,
                role=role,
                content=turn.content,
                metadata=metadata,
            )
            saved_count += 1
        
        if saved_count > 0:
            logger.debug(f"Saved {saved_count} new messages to Foundry thread {thread_id}")
        
        return True
        
    except Exception as e:
        logger.warning(f"Failed to save context to Foundry thread {thread_id}: {e}")
        return False


async def get_or_create_session(
    session_id: str, 
    security: SecurityContext, 
    agent_id: str = "elena"
) -> EnterpriseContext:
    """
    Get existing session or create new one with agent isolation.
    
    When USE_FOUNDRY_THREADS is enabled:
    - Creates/retrieves Foundry thread for persistence
    - Loads conversation history from Foundry
    - Falls back to in-memory sessions if Foundry is unavailable
    
    Each agent gets its own session space per user, ensuring:
    - Elena, Marcus, and Sage have separate conversation threads
    - Users only see their own sessions
    - Project-based access when project_id is specified
    """
    settings = get_settings()
    session_key = _make_session_key(
        user_id=security.user_id,
        agent_id=agent_id,
        session_id=session_id,
        project_id=security.project_id
    )
    
    # Check in-memory cache first (for performance)
    if session_key in _sessions:
        return _sessions[session_key]
    
    # Try Foundry if enabled
    if settings.use_foundry_threads:
        foundry_client = get_foundry_client()
        if foundry_client:
            try:
                # Check if we have a thread ID for this session
                thread_id = _foundry_thread_map.get(session_key)
                
                if thread_id:
                    # Load existing thread
                    context = await _load_context_from_foundry_thread(
                        thread_id, security, agent_id, session_id
                    )
                    if context:
                        _sessions[session_key] = context
                        return context
                else:
                    # Create new Foundry thread
                    thread_id = await foundry_client.create_thread(
                        user_id=security.user_id,
                        agent_id=agent_id,
                        project_id=security.project_id,
                        metadata={
                            "session_id": session_id,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    _foundry_thread_map[session_key] = thread_id
                    logger.info(f"Created Foundry thread {thread_id} for session {session_key}")
                    
                    # Create new context
                    context = EnterpriseContext(security=security)
                    context.episodic.conversation_id = session_id
                    context.episodic.metadata = {
                        "agent_id": agent_id,
                        "project_id": security.project_id,
                        "foundry_thread_id": thread_id,
                    }
                    _sessions[session_key] = context
                    return context
                    
            except Exception as e:
                logger.warning(f"Foundry thread operation failed, falling back to in-memory: {e}")
                # Fall through to in-memory session creation
    
    # Fallback: Create in-memory session
    _sessions[session_key] = EnterpriseContext(security=security)
    _sessions[session_key].episodic.conversation_id = session_id
    _sessions[session_key].episodic.metadata = {
        "agent_id": agent_id,
        "project_id": security.project_id,
    }
    return _sessions[session_key]


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message_id: str
    content: str
    agent_id: str
    agent_name: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    session_id: str
    avatar_video_url: Optional[str] = None  # Foundry avatar video URL (if available)


@router.post("", response_model=ChatResponse)
async def send_message(message: ChatMessage, user: SecurityContext = Depends(get_current_user)):
    """
    Send a message and get a response.

    This is the synchronous endpoint for simple interactions.
    For streaming responses, use the WebSocket endpoint.
    """
    start_time = time.time()

    # Get or create session with agent isolation
    session_id = message.session_id or str(uuid.uuid4())
    agent_id = message.agent_id or "elena"
    context = await get_or_create_session(session_id, user, agent_id=agent_id)

    # Enrich context with memory (with short timeout to avoid blocking)
    try:
        context = await asyncio.wait_for(
            enrich_context(context, message.content),
            timeout=MEMORY_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.warning(f"Memory enrichment timed out after {MEMORY_TIMEOUT}s")
    except Exception as e:
        logger.warning(f"Memory enrichment failed: {e}")

    # Route to agent and get response
    response_text = None
    updated_context = context  # Default to original context
    
    try:
        # Handle legacy or frontend-specific 'model-router' ID
        agent_id_param = message.agent_id
        if agent_id_param == "model-router":
            agent_id_param = None
            
        logger.info(f"Calling agent_chat for user {user.user_id}, session {session_id}, agent {agent_id_param}")
        result = await agent_chat(
            query=message.content, context=context, agent_id=agent_id_param
        )
        
        # Handle both old and new return signatures
        if len(result) == 4:
            response_text, updated_context, used_agent_id, avatar_video_url = result
        else:
            response_text, updated_context, used_agent_id = result
            avatar_video_url = None
        
        logger.info(f"Agent chat succeeded: agent={used_agent_id}, response_length={len(response_text) if response_text else 0}, avatar_video={bool(avatar_video_url)}")

        # Update session with composite key
        session_key = _make_session_key(
            user_id=user.user_id,
            agent_id=used_agent_id,
            session_id=session_id,
            project_id=user.project_id
        )
        _sessions[session_key] = updated_context

        # Persist to memory (fire-and-forget - don't block response)
        async def _persist_with_timeout():
            # Extract user_id explicitly for logging and validation
            user_id = updated_context.security.user_id
            logger.info(f"Background task started: persisting conversation for user: {user_id}")
            try:
                # Save to Foundry thread if enabled
                settings = get_settings()
                if settings.use_foundry_threads:
                    thread_id = _foundry_thread_map.get(session_key)
                    if thread_id:
                        await _save_context_to_foundry_thread(thread_id, updated_context, used_agent_id)
                
                # Persist to Zep memory (existing behavior)
                await asyncio.wait_for(
                    persist_conversation(updated_context),
                    timeout=10.0  # Longer timeout for background task
                )
                logger.info(f"Background task completed: conversation persisted for user: {user_id}")
            except asyncio.TimeoutError:
                logger.warning(f"Memory persistence timed out (background) for user: {user_id}")
            except Exception as e:
                logger.warning(f"Memory persistence failed (background) for user: {user_id}: {e}")

        asyncio.create_task(_persist_with_timeout())

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        # Log detailed error information for debugging
        error_details = str(e)
        if hasattr(e, '__cause__') and e.__cause__:
            error_details += f" (caused by: {e.__cause__})"
        logger.error(f"Error details: {error_details}")
        
        # Log the full traceback for debugging
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Log context information for debugging
        logger.error(f"Context state: session_id={session_id}, user_id={user.user_id}, context_exists={context is not None}")
        if context:
            logger.error(f"Context security: user_id={context.security.user_id}, tenant_id={context.security.tenant_id}")
        
        # Fallback response
        if not response_text:
            response_text = (
                "I apologize, but I encountered an issue processing your request. "
                "Could you please try again? If the problem persists, "
                "the team can check the logs for more details."
            )
    
    # Get agent info (always needed for response)
    try:
        agent = get_agent(used_agent_id)
    except Exception as agent_error:
        logger.error(f"Failed to get agent {agent_id}: {agent_error}")
        agent_id = "elena"
        try:
            agent = get_agent(agent_id)
        except Exception:
            # Last resort - create a minimal agent info
            from backend.agents.base import BaseAgent
            agent = type('FallbackAgent', (BaseAgent,), {
                'agent_id': 'elena',
                'agent_name': 'Elena',
                'agent_title': 'Business Analyst'
            })()

    latency_ms = (time.time() - start_time) * 1000

    return ChatResponse(
        message_id=str(uuid.uuid4()),
        content=response_text,
        agent_id=used_agent_id,
        agent_name=agent.agent_name,
        timestamp=datetime.now(timezone.utc),
        tokens_used=context.operational.total_tokens_used if context else None,
        latency_ms=latency_ms,
        session_id=session_id,
        avatar_video_url=avatar_video_url,  # Include avatar video URL if available
    )


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.session_contexts: dict[str, EnterpriseContext] = {}

    async def connect(self, websocket: WebSocket, session_id: str, security: SecurityContext, agent_id: str = "elena"):
        await websocket.accept()
        # Use composite key for agent isolation
        session_key = _make_session_key(
            user_id=security.user_id,
            agent_id=agent_id,
            session_id=session_id,
            project_id=security.project_id
        )
        self.active_connections[session_key] = websocket
        if session_key not in self.session_contexts:
            context = EnterpriseContext(security=security)
            context.episodic.conversation_id = session_id
            context.episodic.metadata = {
                "agent_id": agent_id,
                "project_id": security.project_id,
            }
            self.session_contexts[session_key] = context

    def disconnect(self, session_key: str):
        if session_key in self.active_connections:
            del self.active_connections[session_key]
        if session_key in self.session_contexts:
            del self.session_contexts[session_key]

    async def send_message(self, session_key: str, message: dict):
        if session_key in self.active_connections:
            await self.active_connections[session_key].send_json(message)

    def get_context(self, session_key: str) -> Optional[EnterpriseContext]:
        return self.session_contexts.get(session_key)

    def update_context(self, session_key: str, context: EnterpriseContext):
        self.session_contexts[session_key] = context


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time streaming chat.

    Protocol:
    - Client sends: {"type": "message", "content": "...", "agent_id": "elena"}
    - Server sends: {"type": "typing", "agent_id": "..."}
    - Server sends: {"type": "chunk", "content": "..."} (streaming)
    - Server sends: {"type": "complete", "message_id": "...", "tokens_used": ...}
    - Server sends: {"type": "error", "message": "..."}
    
    Authentication: Extract JWT token from query parameter since WebSockets
    cannot send Authorization headers. Validate token and extract user identity.
    """
    await websocket.accept()
    logger.info(f"Chat WebSocket connected: {session_id}")
    
    # Extract token from query parameter
    token_param = websocket.query_params.get("token")
    settings = get_settings()  # Already imported above
    
    # Determine user_id based on auth requirements
    if settings.auth_required:
        if not token_param:
            logger.warning(f"Chat WebSocket: Authentication required but no token provided for session {session_id}")
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Validate token
        try:
            from backend.api.middleware.auth import get_auth
            auth = get_auth()
            token = await auth.validate_token(token_param)
            user_id = token.oid
            tenant_id = token.tid
            email = token.email
            display_name = token.name
            roles = auth.map_roles(token.roles)
            scopes = auth.extract_scopes(token)
            logger.info(f"Chat WebSocket: Authenticated user {user_id} for session {session_id}")
        except Exception as e:
            logger.warning(f"Chat WebSocket: Token validation failed for session {session_id}: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return
    else:
        # POC mode: use default user when auth not required
        from backend.core import Role
        user_id = "poc-user"
        tenant_id = settings.azure_tenant_id or "poc-tenant"
        email = None
        display_name = None
        roles = [Role.ADMIN]
        scopes = ["*"]
        logger.info(f"Chat WebSocket: Using POC user for session {session_id} (AUTH_REQUIRED=false)")

    # Create SecurityContext with authenticated user
    security = SecurityContext(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        scopes=scopes,
        session_id=session_id,
        email=email,
        display_name=display_name,
    )

    # Extract agent_id from initial connection or default to elena
    agent_id = "elena"  # Default, will be updated from messages
    session_key = _make_session_key(
        user_id=security.user_id,
        agent_id=agent_id,
        session_id=session_id,
        project_id=security.project_id
    )
    await manager.connect(websocket, session_id, security, agent_id=agent_id)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "")
                agent_id = data.get("agent_id", "elena")
                
                # Update session key if agent changed
                session_key = _make_session_key(
                    user_id=security.user_id,
                    agent_id=agent_id,
                    session_id=session_id,
                    project_id=security.project_id
                )

                # Get context (may need to create if agent switched)
                context = manager.get_context(session_key)
                if not context:
                    # Agent switched - create new context for this agent
                    context = await get_or_create_session(session_id, security, agent_id=agent_id)
                    manager.update_context(session_key, context)
                if not context:
                    await manager.send_message(session_key, {"type": "error", "message": "Session not found"})
                    continue

                # Send typing indicator
                await manager.send_message(session_key, {"type": "typing", "agent_id": agent_id})

                try:
                    # Enrich context
                    context = await enrich_context(context, content)

                    # Get response from agent
                    start_time = time.time()
                    response_text, updated_context, used_agent_id = await agent_chat(
                        query=content, context=context, agent_id=agent_id
                    )
                    latency_ms = (time.time() - start_time) * 1000

                    # Update context
                    manager.update_context(session_key, updated_context)

                    # Persist to Foundry thread if enabled
                    settings = get_settings()
                    if settings.use_foundry_threads:
                        thread_id = _foundry_thread_map.get(session_key)
                        if thread_id:
                            await _save_context_to_foundry_thread(thread_id, updated_context, used_agent_id)

                    # Persist to memory
                    await persist_conversation(updated_context)

                    # Send response (simulating streaming with word chunks)
                    words = response_text.split()
                    chunk_size = 5
                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i : i + chunk_size])
                        await manager.send_message(
                            session_key,
                            {
                                "type": "chunk",
                                "content": chunk + " ",
                                "agent_id": used_agent_id,
                            },
                        )

                    # Send completion
                    await manager.send_message(
                        session_key,
                        {
                            "type": "complete",
                            "message_id": str(uuid.uuid4()),
                            "agent_id": used_agent_id,
                            "tokens_used": updated_context.operational.total_tokens_used,
                            "latency_ms": latency_ms,
                        },
                    )

                except Exception as e:
                    logger.error(f"WebSocket chat error: {e}")
                    await manager.send_message(
                        session_key,
                        {"type": "error", "message": "Failed to process message"},
                    )

    except WebSocketDisconnect:
        manager.disconnect(session_key)
        logger.info(f"WebSocket disconnected: {session_key}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str, 
    agent_id: str = "elena",
    user: SecurityContext = Depends(get_current_user)
):
    """
    Clear a chat session for a specific agent.
    
    Since each agent has separate sessions, you must specify which agent's session to clear.
    When USE_FOUNDRY_THREADS is enabled, this also deletes the Foundry thread.
    """
    session_key = _make_session_key(
        user_id=user.user_id,
        agent_id=agent_id,
        session_id=session_id,
        project_id=user.project_id
    )
    
    # Delete Foundry thread if enabled
    settings = get_settings()
    if settings.use_foundry_threads:
        foundry_client = get_foundry_client()
        if foundry_client:
            thread_id = _foundry_thread_map.get(session_key)
            if thread_id:
                try:
                    await foundry_client.delete_thread(thread_id)
                    logger.info(f"Deleted Foundry thread {thread_id} for session {session_key}")
                except Exception as e:
                    logger.warning(f"Failed to delete Foundry thread {thread_id}: {e}")
                finally:
                    # Remove from map even if deletion failed
                    _foundry_thread_map.pop(session_key, None)
    
    # Clear in-memory sessions
    if session_key in _sessions:
        del _sessions[session_key]
    if session_key in manager.session_contexts:
        del manager.session_contexts[session_key]

    return {"success": True, "message": f"Session {session_id} cleared for agent {agent_id}"}
