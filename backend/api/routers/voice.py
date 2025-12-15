"""
Voice Router

Provides voice endpoints with chat-based fallback:
- WebSocket endpoint for voice interaction using agents
- REST endpoints for voice configuration

Note: When VoiceLive realtime endpoint is not available, uses chat completions
with the agent system for text responses.
"""

import asyncio
import base64
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from backend.voice.voicelive_service import voicelive_service
from backend.core import get_settings, EnterpriseContext, SecurityContext, Role
from backend.agents import chat as agent_chat, get_agent

logger = logging.getLogger(__name__)

router = APIRouter()


class VoiceConfigResponse(BaseModel):
    """Voice configuration response"""
    agent_id: str
    voice_name: str
    model: str
    endpoint_configured: bool


class VoiceLiveSessionManager:
    """Manages VoiceLive WebSocket sessions"""
    
    def __init__(self):
        self.active_sessions: dict[str, dict] = {}
    
    def create_session(self, session_id: str, agent_id: str = "elena") -> dict:
        """Create a new VoiceLive session"""
        config = voicelive_service.get_agent_voice_config(agent_id)
        session = {
            "session_id": session_id,
            "agent_id": agent_id,
            "voice_config": config,
            "voicelive_connection": None,
            "is_speaking": False,
        }
        self.active_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get an existing session"""
        return self.active_sessions.get(session_id)
    
    def update_agent(self, session_id: str, agent_id: str) -> Optional[dict]:
        """Update the agent for a session"""
        session = self.active_sessions.get(session_id)
        if session:
            config = voicelive_service.get_agent_voice_config(agent_id)
            session["agent_id"] = agent_id
            session["voice_config"] = config
        return session
    
    def remove_session(self, session_id: str):
        """Remove a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


session_manager = VoiceLiveSessionManager()


@router.get("/config/{agent_id}", response_model=VoiceConfigResponse)
async def get_voice_config(agent_id: str):
    """Get voice configuration for an agent"""
    config = voicelive_service.get_agent_voice_config(agent_id)
    
    return VoiceConfigResponse(
        agent_id=agent_id,
        voice_name=config.voice_name,
        model=voicelive_service.model,
        endpoint_configured=voicelive_service.is_configured,
    )


@router.websocket("/voicelive/{session_id}")
async def voicelive_websocket(websocket: WebSocket, session_id: str):
    """
    VoiceLive WebSocket endpoint for real-time voice interaction.
    
    Protocol:
    Client → Server:
    - {"type": "audio", "data": "<base64 PCM16>"} - Audio chunk from microphone
    - {"type": "agent", "agent_id": "elena|marcus"} - Switch agent
    - {"type": "cancel"} - Cancel current response
    
    Server → Client:
    - {"type": "transcription", "status": "listening|processing|complete", "text": "..."}
    - {"type": "audio", "data": "<base64>", "format": "audio/wav"}
    - {"type": "agent_switched", "agent_id": "..."}
    - {"type": "error", "message": "..."}
    """
    await websocket.accept()
    logger.info(f"VoiceLive WebSocket connected: {session_id}")
    
    # Create session with default agent
    session = session_manager.create_session(session_id, "elena")
    
    # Check if VoiceLive is configured
    if not voicelive_service.is_configured:
        await websocket.send_json({
            "type": "error",
            "message": "VoiceLive not configured. Set AZURE_VOICELIVE_ENDPOINT and AZURE_VOICELIVE_KEY."
        })
        await websocket.close()
        return
    
    voicelive_task = None
    
    try:
        # Import VoiceLive SDK
        from azure.core.credentials import AzureKeyCredential
        from azure.ai.voicelive.aio import connect
        from azure.ai.voicelive.models import (
            RequestSession, Modality, InputAudioFormat, OutputAudioFormat,
            ServerVad, ServerEventType, AzureStandardVoice
        )
        
        # Get agent configuration
        agent_config = session["voice_config"]
        
        # Get VoiceLive credential
        credential = AzureKeyCredential(voicelive_service.key)
        
        # Connect to VoiceLive
        async with connect(
            endpoint=voicelive_service.endpoint,
            credential=credential,
            model=voicelive_service.model,
        ) as voicelive_connection:
            
            # Configure session
            session_config = RequestSession(
                modalities=[Modality.TEXT, Modality.AUDIO],
                instructions=agent_config.instructions,
                input_audio_format=InputAudioFormat.PCM16,
                output_audio_format=OutputAudioFormat.PCM16,
                voice=AzureStandardVoice(name=agent_config.voice_name),
                turn_detection=ServerVad(
                    threshold=0.5,
                    prefix_padding_ms=300,
                    silence_duration_ms=500,
                ),
            )
            await voicelive_connection.session.update(session=session_config)
            
            # Send ready message
            await websocket.send_json({
                "type": "agent_switched",
                "agent_id": session["agent_id"],
            })
            
            # Create task to process VoiceLive events
            async def process_voicelive_events():
                try:
                    async for event in voicelive_connection:
                        if event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                            await websocket.send_json({
                                "type": "transcription",
                                "status": "listening",
                            })
                        
                        elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
                            await websocket.send_json({
                                "type": "transcription",
                                "status": "processing",
                            })
                        
                        elif event.type == ServerEventType.RESPONSE_AUDIO_DELTA:
                            # Send audio chunk to client
                            audio_base64 = base64.b64encode(event.delta).decode("utf-8")
                            await websocket.send_json({
                                "type": "audio",
                                "data": audio_base64,
                                "format": "audio/pcm16",
                            })
                        
                        elif event.type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                            # Send transcript
                            await websocket.send_json({
                                "type": "transcription",
                                "status": "complete",
                                "text": event.delta if hasattr(event, 'delta') else "",
                            })
                        
                        elif event.type == ServerEventType.ERROR:
                            error_msg = event.error.message if hasattr(event, 'error') else "Unknown error"
                            await websocket.send_json({
                                "type": "error",
                                "message": error_msg,
                            })
                            
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"VoiceLive event processing error: {e}")
            
            voicelive_task = asyncio.create_task(process_voicelive_events())
            
            # Main message loop
            try:
                while True:
                    data = await websocket.receive_json()
                    msg_type = data.get("type")
                    
                    if msg_type == "audio":
                        # Forward audio to VoiceLive
                        audio_data = base64.b64decode(data.get("data", ""))
                        await voicelive_connection.input_audio_buffer.append(audio=audio_data)
                    
                    elif msg_type == "agent":
                        # Switch agent
                        new_agent_id = data.get("agent_id", "elena")
                        session_manager.update_agent(session_id, new_agent_id)
                        agent_config = voicelive_service.get_agent_voice_config(new_agent_id)
                        
                        # Update session configuration
                        new_session_config = RequestSession(
                            modalities=[Modality.TEXT, Modality.AUDIO],
                            instructions=agent_config.instructions,
                            voice=AzureStandardVoice(name=agent_config.voice_name),
                            input_audio_format=InputAudioFormat.PCM16,
                            output_audio_format=OutputAudioFormat.PCM16,
                            turn_detection=ServerVad(
                                threshold=0.5,
                                prefix_padding_ms=300,
                                silence_duration_ms=500,
                            ),
                        )
                        await voicelive_connection.session.update(session=new_session_config)
                        
                        await websocket.send_json({
                            "type": "agent_switched",
                            "agent_id": new_agent_id,
                        })
                    
                    elif msg_type == "cancel":
                        # Cancel current response
                        await voicelive_connection.response.cancel()
                    
            except WebSocketDisconnect:
                logger.info(f"VoiceLive WebSocket disconnected: {session_id}")
            
            finally:
                if voicelive_task:
                    voicelive_task.cancel()
                    try:
                        await voicelive_task
                    except asyncio.CancelledError:
                        pass
    
    except ImportError as e:
        logger.error(f"VoiceLive SDK not installed: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "VoiceLive SDK not installed. Install with: pip install azure-ai-voicelive[aiohttp]",
        })
        await websocket.close()
    
    except Exception as e:
        logger.error(f"VoiceLive connection error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"VoiceLive connection failed: {str(e)}",
        })
        await websocket.close()
    
    finally:
        session_manager.remove_session(session_id)
        logger.info(f"VoiceLive session cleaned up: {session_id}")


@router.get("/status")
async def get_voice_status():
    """Get VoiceLive service status"""
    return {
        "voicelive_configured": voicelive_service.is_configured,
        "endpoint": voicelive_service.endpoint[:50] + "..." if voicelive_service.endpoint else None,
        "model": voicelive_service.model,
        "active_sessions": len(session_manager.active_sessions),
        "agents": {
            "elena": {
                "voice": voicelive_service.get_agent_voice_config("elena").voice_name,
            },
            "marcus": {
                "voice": voicelive_service.get_agent_voice_config("marcus").voice_name,
            },
        },
    }
