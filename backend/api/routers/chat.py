"""
Chat endpoints

Provides:
- REST endpoint for single-turn chat
- WebSocket endpoint for streaming chat
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.core import EnterpriseContext, MessageRole, Turn

router = APIRouter()


class ChatMessage(BaseModel):
    content: str
    agent_id: Optional[str] = "elena"


class ChatResponse(BaseModel):
    message_id: str
    content: str
    agent_id: str
    agent_name: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


@router.post("", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """
    Send a message and get a response.
    
    This is the synchronous endpoint for simple interactions.
    For streaming responses, use the WebSocket endpoint.
    """
    # TODO: Implement full agent pipeline
    # For now, return a placeholder response
    
    import uuid
    from datetime import datetime
    import time
    
    start_time = time.time()
    
    # Placeholder response based on agent
    if message.agent_id == "marcus":
        agent_name = "Marcus Chen"
        response_content = (
            "Thanks for reaching out! I'd be happy to help with project planning. "
            "To give you the best guidance, could you tell me more about:\n"
            "- What's the scope of the project?\n"
            "- What's your target timeline?\n"
            "- Who are the key stakeholders involved?"
        )
    else:
        agent_name = "Dr. Elena Vasquez"
        response_content = (
            "I'd be glad to help you analyze this. Let me ask a few clarifying questions "
            "to make sure I understand the full context:\n"
            "- What's the primary business goal you're trying to achieve?\n"
            "- Who are the main stakeholders affected?\n"
            "- Are there any constraints or dependencies I should know about?"
        )
    
    latency_ms = (time.time() - start_time) * 1000
    
    return ChatResponse(
        message_id=str(uuid.uuid4()),
        content=response_content,
        agent_id=message.agent_id or "elena",
        agent_name=agent_name,
        timestamp=datetime.utcnow(),
        tokens_used=150,  # Placeholder
        latency_ms=latency_ms,
    )


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time streaming chat.
    
    Protocol:
    - Client sends: {"type": "message", "content": "...", "agent_id": "elena"}
    - Server sends: {"type": "chunk", "content": "..."} (streaming)
    - Server sends: {"type": "complete", "message_id": "...", "tokens_used": ...}
    - Server sends: {"type": "error", "message": "..."}
    """
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                content = data.get("content", "")
                agent_id = data.get("agent_id", "elena")
                
                # TODO: Implement streaming response from agent
                # For now, send a placeholder response
                
                # Simulate streaming chunks
                response_words = [
                    "I", "understand", "your", "question.", 
                    "Let", "me", "think", "about", "this..."
                ]
                
                for word in response_words:
                    await manager.send_message(session_id, {
                        "type": "chunk",
                        "content": word + " ",
                        "agent_id": agent_id
                    })
                
                # Send completion
                await manager.send_message(session_id, {
                    "type": "complete",
                    "message_id": session_id,
                    "tokens_used": 50,
                    "latency_ms": 100
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)

