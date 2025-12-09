"""
Chat endpoints

Provides:
- REST endpoint for single-turn chat
- WebSocket endpoint for streaming chat
- Integration with LangGraph agents and Zep memory
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.agents import chat as agent_chat, get_agent
from backend.api.middleware.auth import get_current_user
from backend.core import EnterpriseContext, SecurityContext
from backend.memory import enrich_context, persist_conversation

logger = logging.getLogger(__name__)

router = APIRouter()


# Session storage (in production, use Redis or similar)
_sessions: dict[str, EnterpriseContext] = {}


def get_or_create_session(
    session_id: str,
    security: SecurityContext
) -> EnterpriseContext:
    """Get existing session or create new one"""
    if session_id not in _sessions:
        _sessions[session_id] = EnterpriseContext(security=security)
        _sessions[session_id].episodic.conversation_id = session_id
    return _sessions[session_id]


class ChatMessage(BaseModel):
    content: str
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


@router.post("", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Send a message and get a response.
    
    This is the synchronous endpoint for simple interactions.
    For streaming responses, use the WebSocket endpoint.
    """
    start_time = time.time()
    
    # Get or create session
    session_id = message.session_id or str(uuid.uuid4())
    context = get_or_create_session(session_id, user)
    
    # Enrich context with memory
    try:
        context = await enrich_context(context, message.content)
    except Exception as e:
        logger.warning(f"Memory enrichment failed: {e}")
    
    # Route to agent and get response
    try:
        response_text, updated_context, agent_id = await agent_chat(
            query=message.content,
            context=context,
            agent_id=message.agent_id
        )
        
        # Update session
        _sessions[session_id] = updated_context
        
        # Persist to memory
        try:
            await persist_conversation(updated_context)
        except Exception as e:
            logger.warning(f"Memory persistence failed: {e}")
        
        # Get agent info
        agent = get_agent(agent_id)
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        # Fallback response
        agent_id = message.agent_id or "elena"
        agent = get_agent(agent_id)
        response_text = (
            "I apologize, but I encountered an issue processing your request. "
            "Could you please try again? If the problem persists, "
            "the team can check the logs for more details."
        )
    
    latency_ms = (time.time() - start_time) * 1000
    
    return ChatResponse(
        message_id=str(uuid.uuid4()),
        content=response_text,
        agent_id=agent_id,
        agent_name=agent.agent_name,
        timestamp=datetime.utcnow(),
        tokens_used=context.operational.total_tokens_used if context else None,
        latency_ms=latency_ms,
        session_id=session_id
    )


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.session_contexts: dict[str, EnterpriseContext] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        session_id: str,
        security: SecurityContext
    ):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        if session_id not in self.session_contexts:
            context = EnterpriseContext(security=security)
            context.episodic.conversation_id = session_id
            self.session_contexts[session_id] = context
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)
    
    def get_context(self, session_id: str) -> Optional[EnterpriseContext]:
        return self.session_contexts.get(session_id)
    
    def update_context(self, session_id: str, context: EnterpriseContext):
        self.session_contexts[session_id] = context


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
    """
    # For WebSocket, create a dev security context
    # In production, validate token from query params or first message
    from backend.core import Role
    dev_security = SecurityContext(
        user_id="ws-user",
        tenant_id="ws-tenant",
        roles=[Role.ANALYST],
        scopes=["*"]
    )
    
    await manager.connect(websocket, session_id, dev_security)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                content = data.get("content", "")
                agent_id = data.get("agent_id", "elena")
                
                # Get context
                context = manager.get_context(session_id)
                if not context:
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": "Session not found"
                    })
                    continue
                
                # Send typing indicator
                await manager.send_message(session_id, {
                    "type": "typing",
                    "agent_id": agent_id
                })
                
                try:
                    # Enrich context
                    context = await enrich_context(context, content)
                    
                    # Get response from agent
                    start_time = time.time()
                    response_text, updated_context, used_agent_id = await agent_chat(
                        query=content,
                        context=context,
                        agent_id=agent_id
                    )
                    latency_ms = (time.time() - start_time) * 1000
                    
                    # Update context
                    manager.update_context(session_id, updated_context)
                    
                    # Persist to memory
                    await persist_conversation(updated_context)
                    
                    # Send response (simulating streaming with word chunks)
                    words = response_text.split()
                    chunk_size = 5
                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i:i+chunk_size])
                        await manager.send_message(session_id, {
                            "type": "chunk",
                            "content": chunk + " ",
                            "agent_id": used_agent_id
                        })
                    
                    # Send completion
                    await manager.send_message(session_id, {
                        "type": "complete",
                        "message_id": str(uuid.uuid4()),
                        "agent_id": used_agent_id,
                        "tokens_used": updated_context.operational.total_tokens_used,
                        "latency_ms": latency_ms
                    })
                    
                except Exception as e:
                    logger.error(f"WebSocket chat error: {e}")
                    await manager.send_message(session_id, {
                        "type": "error",
                        "message": "Failed to process message"
                    })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    user: SecurityContext = Depends(get_current_user)
):
    """Clear a chat session"""
    if session_id in _sessions:
        del _sessions[session_id]
    if session_id in manager.session_contexts:
        del manager.session_contexts[session_id]
    
    return {"success": True, "message": f"Session {session_id} cleared"}
