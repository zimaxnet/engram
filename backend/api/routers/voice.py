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
from backend.core import get_settings, EnterpriseContext, SecurityContext, Role, MessageRole, Turn
from backend.agents import chat as agent_chat, get_agent
from backend.memory import memory_client, persist_conversation

logger = logging.getLogger(__name__)

router = APIRouter()

# Timeouts for memory operations (seconds) - keep VoiceLive real-time loop responsive
VOICE_MEMORY_TIMEOUT = 2.0
VOICE_PERSIST_TIMEOUT = 10.0


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

    # ---------------------------------------------------------------------
    # Memory: create an EnterpriseContext for this VoiceLive session so that
    # user/assistant transcripts can be persisted into Zep as episodic memory.
    #
    # Note: WebSockets from browsers cannot set custom Authorization headers.
    # For now we use a POC identity when AUTH_REQUIRED=false. When AUTH_REQUIRED=true,
    # you should enforce Entra auth for WebSockets (e.g., token in query param or cookie).
    # ---------------------------------------------------------------------
    settings = get_settings()
    if not settings.auth_required:
        security = SecurityContext(
            user_id="poc-user",
            tenant_id=settings.azure_tenant_id or "poc-tenant",
            roles=[Role.ADMIN],
            scopes=["*"],
            session_id=session_id,
            token_expiry=None,
            email=None,
            display_name=None,
        )
    else:
        # Future: validate Entra token for WS and map to SecurityContext.
        # Keeping a safe default here avoids silently writing cross-tenant memory.
        security = SecurityContext(
            user_id="voice-user",
            tenant_id=settings.azure_tenant_id or "unknown-tenant",
            roles=[Role.ANALYST],
            scopes=["*"],
            session_id=session_id,
            token_expiry=None,
            email=None,
            display_name=None,
        )

    voice_context = EnterpriseContext(security=security, context_version="1.0.0")
    voice_context.episodic.conversation_id = session_id
    session["context"] = voice_context

    async def _ensure_memory_session():
        try:
            await asyncio.wait_for(
                memory_client.get_or_create_session(
                    session_id=session_id,
                    user_id=security.user_id,
                    metadata={
                        "tenant_id": security.tenant_id,
                        "channel": "voice",
                        "agent_id": session.get("agent_id", "elena"),
                    },
                ),
                timeout=VOICE_MEMORY_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning("Voice memory session init timed out")
        except Exception as e:
            logger.warning(f"Voice memory session init failed: {e}")

    asyncio.create_task(_ensure_memory_session())
    
    # Check if VoiceLive is configured
    if not voicelive_service.is_configured:
        await websocket.send_json({
            "type": "error",
            "message": "VoiceLive not configured. Set AZURE_VOICELIVE_ENDPOINT and provide auth (AZURE_VOICELIVE_KEY or Managed Identity)."
        })
        await websocket.close()
        return
    
    voicelive_task = None
    
    try:
        # Import VoiceLive SDK
        from azure.ai.voicelive.aio import connect  # type: ignore[import-not-found]
        from azure.ai.voicelive.models import (  # type: ignore[import-not-found]
            RequestSession, Modality, InputAudioFormat, OutputAudioFormat,
            ServerVad, ServerEventType, AzureStandardVoice
        )
        
        # Get agent configuration
        agent_config = session["voice_config"]
        
        # Get VoiceLive credential
        credential = voicelive_service.get_credential()
        
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
                # Buffers for accumulating transcript deltas into complete turns
                user_transcript_buf = ""
                assistant_text_buf = ""
                assistant_audio_transcript_buf = ""
                # Per-response flags to avoid duplicate UI emits / duplicate memory persistence
                assistant_text_seen = False
                assistant_turn_committed = False
                assistant_transcript_final_sent = False

                async def _persist_latest_turns():
                    """Best-effort persistence of the latest user+assistant turns into Zep."""
                    try:
                        await asyncio.wait_for(
                            persist_conversation(voice_context),
                            timeout=VOICE_PERSIST_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        logger.warning("Voice memory persistence timed out (background)")
                    except Exception as e:
                        logger.warning(f"Voice memory persistence failed (background): {e}")

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
                        
                        elif event.type == ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_DELTA:
                            # User speech-to-text (partial)
                            delta = getattr(event, "delta", "") or ""
                            user_transcript_buf += str(delta)
                            await websocket.send_json({
                                "type": "transcription",
                                "speaker": "user",
                                "status": "processing",
                                "text": user_transcript_buf,
                            })

                        elif event.type == ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                            # User speech-to-text (final)
                            final_text = (
                                getattr(event, "transcript", None)
                                or getattr(event, "text", None)
                                or getattr(event, "delta", None)
                                or user_transcript_buf
                                or ""
                            )
                            final_text = str(final_text).strip()
                            user_transcript_buf = ""

                            if final_text:
                                # Send to UI as "You said"
                                await websocket.send_json({
                                    "type": "transcription",
                                    "speaker": "user",
                                    "status": "complete",
                                    "text": final_text,
                                })

                                # Store as episodic memory (user turn)
                                voice_context.episodic.add_turn(
                                    Turn(
                                        role=MessageRole.USER,
                                        content=final_text,
                                        agent_id=None,
                                        tool_calls=None,
                                        token_count=None,
                                    )
                                )

                        elif event.type == ServerEventType.RESPONSE_CREATED:
                            # New assistant response: reset per-response buffers/flags to avoid
                            # cross-response transcript bleed and duplicate persistence.
                            assistant_text_buf = ""
                            assistant_audio_transcript_buf = ""
                            assistant_text_seen = False
                            assistant_turn_committed = False
                            assistant_transcript_final_sent = False

                        elif event.type == ServerEventType.RESPONSE_AUDIO_DELTA:
                            # Send audio chunk to client
                            audio_base64 = base64.b64encode(event.delta).decode("utf-8")
                            await websocket.send_json({
                                "type": "audio",
                                "data": audio_base64,
                                "format": "audio/pcm16",
                            })
                        
                        elif event.type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                            delta = getattr(event, "delta", "") or ""
                            if delta:
                                assistant_audio_transcript_buf += str(delta)
                                # Stream assistant transcript to UI only when text events aren't available.
                                if not assistant_text_seen:
                                    await websocket.send_json({
                                        "type": "transcription",
                                        "speaker": "assistant",
                                        "status": "processing",
                                        "text": assistant_audio_transcript_buf,
                                    })

                        elif event.type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DONE:
                            final_text = (
                                getattr(event, "transcript", None)
                                or getattr(event, "text", None)
                                or assistant_audio_transcript_buf
                                or ""
                            )
                            final_text = str(final_text).strip()
                            assistant_audio_transcript_buf = final_text

                            # If we didn't get RESPONSE_TEXT_* events, treat audio transcript as canonical.
                            if final_text and not assistant_text_seen:
                                if not assistant_transcript_final_sent:
                                    await websocket.send_json({
                                        "type": "transcription",
                                        "speaker": "assistant",
                                        "status": "complete",
                                        "text": final_text,
                                    })
                                    assistant_transcript_final_sent = True

                                if not assistant_turn_committed:
                                    voice_context.episodic.add_turn(
                                        Turn(
                                            role=MessageRole.ASSISTANT,
                                            content=final_text,
                                            agent_id=session.get("agent_id", "elena"),
                                            tool_calls=None,
                                            token_count=None,
                                        )
                                    )
                                    assistant_turn_committed = True
                                    asyncio.create_task(_persist_latest_turns())

                        elif event.type == ServerEventType.RESPONSE_TEXT_DELTA:
                            # Assistant text output (partial)
                            delta = getattr(event, "delta", "") or ""
                            if delta:
                                assistant_text_seen = True
                                assistant_text_buf += str(delta)
                                await websocket.send_json({
                                    "type": "transcription",
                                    "speaker": "assistant",
                                    "status": "processing",
                                    "text": assistant_text_buf,
                                })

                        elif event.type == ServerEventType.RESPONSE_TEXT_DONE:
                            # Assistant text output (final)
                            final_text = (
                                getattr(event, "text", None)
                                or getattr(event, "delta", None)
                                or assistant_text_buf
                                or ""
                            )
                            final_text = str(final_text).strip()
                            assistant_text_buf = ""
                            assistant_text_seen = True
                            # Clear audio transcript buffer to prevent RESPONSE_DONE fallback from
                            # duplicating the assistant turn when audio transcript content exists.
                            assistant_audio_transcript_buf = ""

                            if final_text:
                                await websocket.send_json({
                                    "type": "transcription",
                                    "speaker": "assistant",
                                    "status": "complete",
                                    "text": final_text,
                                })
                                assistant_transcript_final_sent = True

                                voice_context.episodic.add_turn(
                                    Turn(
                                        role=MessageRole.ASSISTANT,
                                        content=final_text,
                                        agent_id=session.get("agent_id", "elena"),
                                        tool_calls=None,
                                        token_count=None,
                                    )
                                )
                                assistant_turn_committed = True
                                asyncio.create_task(_persist_latest_turns())

                        elif event.type == ServerEventType.RESPONSE_DONE:
                            # Final fallback: if we still haven't committed an assistant turn,
                            # persist whatever transcript we have (text preferred, then audio).
                            if not assistant_turn_committed:
                                fallback_text = (assistant_text_buf or assistant_audio_transcript_buf or "").strip()
                                if fallback_text:
                                    if not assistant_transcript_final_sent:
                                        await websocket.send_json({
                                            "type": "transcription",
                                            "speaker": "assistant",
                                            "status": "complete",
                                            "text": fallback_text,
                                        })
                                        assistant_transcript_final_sent = True

                                    voice_context.episodic.add_turn(
                                        Turn(
                                            role=MessageRole.ASSISTANT,
                                            content=fallback_text,
                                            agent_id=session.get("agent_id", "elena"),
                                            tool_calls=None,
                                            token_count=None,
                                        )
                                    )
                                    assistant_turn_committed = True
                                    asyncio.create_task(_persist_latest_turns())

                            # Always clear buffers at end of response.
                            assistant_text_buf = ""
                            assistant_audio_transcript_buf = ""
                        
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