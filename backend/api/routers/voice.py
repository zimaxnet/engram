"""
Voice and Avatar API endpoints

Provides:
- Speech-to-text transcription
- Text-to-speech synthesis
- Avatar session management
- Real-time voice chat
"""

import asyncio
import base64
import logging
import time
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Speech-to-Text Endpoints
# =============================================================================


class TranscriptionResponse(BaseModel):
    text: str
    confidence: float
    duration_ms: int
    language: str


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "en-US",
    user: SecurityContext = Depends(get_current_user),
):
    """
    Transcribe audio to text using Azure Speech Services.

    Accepts WAV or MP3 audio files.
    """
    try:
        from backend.voice import recognize_speech

        # Read audio data
        audio_data = await audio.read()

        # Transcribe
        result = await recognize_speech(audio_data, language)

        return TranscriptionResponse(
            text=result.text,
            confidence=result.confidence,
            duration_ms=result.duration_ms,
            language=language,
        )

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")


# =============================================================================
# Text-to-Speech Endpoints
# =============================================================================


class SynthesizeRequest(BaseModel):
    text: str
    agent_id: str = "elena"
    include_visemes: bool = True


class SynthesizeResponse(BaseModel):
    audio_base64: str
    audio_format: str
    duration_ms: int
    visemes: list[dict]


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(
    request: SynthesizeRequest, user: SecurityContext = Depends(get_current_user)
):
    """
    Synthesize speech from text using Azure Speech Services.

    Returns audio data and viseme timings for lip-sync.
    """
    try:
        from backend.voice import synthesize_speech as synth, get_voice_for_agent

        voice_id = get_voice_for_agent(request.agent_id)

        result = await synth(
            text=request.text,
            voice_id=voice_id,
            include_visemes=request.include_visemes,
        )

        # Encode audio as base64
        audio_base64 = (
            base64.b64encode(result.audio_data).decode("utf-8")
            if result.audio_data
            else ""
        )

        return SynthesizeResponse(
            audio_base64=audio_base64,
            audio_format=result.audio_format,
            duration_ms=result.duration_ms,
            visemes=result.visemes,
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")


# =============================================================================
# Avatar Session Endpoints
# =============================================================================


class CreateAvatarSessionRequest(BaseModel):
    agent_id: str = "elena"


class AvatarSessionResponse(BaseModel):
    session_id: str
    agent_id: str
    webrtc_config: dict
    is_active: bool


@router.post("/avatar/session", response_model=AvatarSessionResponse)
async def create_avatar_session(
    request: CreateAvatarSessionRequest,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Create a new avatar session for real-time rendering.

    Returns WebRTC configuration for client connection.
    """
    try:
        from backend.voice import create_avatar_session, avatar_service

        session_id = str(uuid.uuid4())
        session = await create_avatar_session(session_id, request.agent_id)

        return AvatarSessionResponse(
            session_id=session.session_id,
            agent_id=session.agent_id,
            webrtc_config=avatar_service.get_webrtc_config(session),
            is_active=session.is_active,
        )

    except Exception as e:
        logger.error(f"Failed to create avatar session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create avatar session")


@router.get("/avatar/session/{session_id}", response_model=AvatarSessionResponse)
async def get_avatar_session(
    session_id: str, user: SecurityContext = Depends(get_current_user)
):
    """Get an existing avatar session"""
    try:
        from backend.voice import get_avatar_session as get_session, avatar_service

        session = await get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return AvatarSessionResponse(
            session_id=session.session_id,
            agent_id=session.agent_id,
            webrtc_config=avatar_service.get_webrtc_config(session),
            is_active=session.is_active,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get avatar session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get avatar session")


@router.delete("/avatar/session/{session_id}")
async def close_avatar_session(
    session_id: str, user: SecurityContext = Depends(get_current_user)
):
    """Close an avatar session"""
    try:
        from backend.voice import close_avatar_session as close_session

        success = await close_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "message": "Session closed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close avatar session: {e}")
        raise HTTPException(status_code=500, detail="Failed to close avatar session")


class AvatarSpeakRequest(BaseModel):
    text: str


class AvatarSpeakResponse(BaseModel):
    success: bool
    duration_ms: int
    visemes: list[dict]


@router.post("/avatar/session/{session_id}/speak", response_model=AvatarSpeakResponse)
async def avatar_speak(
    session_id: str,
    request: AvatarSpeakRequest,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Make the avatar speak with lip-sync animation.
    """
    try:
        from backend.voice import (
            avatar_speak as speak,
            get_avatar_session,
            get_voice_for_agent,
            synthesize_speech,
        )

        # Get session
        session = await get_avatar_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Synthesize speech to get visemes
        voice_id = get_voice_for_agent(session.agent_id)
        synth_result = await synthesize_speech(
            text=request.text, voice_id=voice_id, include_visemes=True
        )

        # Make avatar speak
        speak_result = await speak(
            session_id=session_id, text=request.text, visemes=synth_result.visemes
        )

        return AvatarSpeakResponse(
            success=speak_result.success,
            duration_ms=speak_result.duration_ms,
            visemes=synth_result.visemes,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar speak failed: {e}")
        raise HTTPException(status_code=500, detail="Avatar speak failed")


class AvatarExpressionRequest(BaseModel):
    expression: str  # "smile", "neutral", "thinking", etc.


@router.post("/avatar/session/{session_id}/expression")
async def set_avatar_expression(
    session_id: str,
    request: AvatarExpressionRequest,
    user: SecurityContext = Depends(get_current_user),
):
    """Set the avatar's facial expression"""
    try:
        from backend.voice import avatar_service

        success = await avatar_service.set_expression(session_id, request.expression)

        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"success": True, "expression": request.expression}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set expression: {e}")
        raise HTTPException(status_code=500, detail="Failed to set expression")


# =============================================================================
# Real-time Voice Chat WebSocket
# =============================================================================


@router.websocket("/voicelive/{session_id}")
async def voicelive_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket for Azure VoiceLive real-time voice conversation with avatar support.

    Supports both Elena (Business Analyst) and Marcus (Project Manager).
    This is the PRIMARY and ONLY voice interaction endpoint.

    Protocol:
    - Client sends: {"type": "audio", "data": "<base64 PCM16 audio>"}
    - Client sends: {"type": "agent", "agent_id": "elena|marcus"} (to switch agent)
    - Client sends: {"type": "text", "text": "..."} (optional text input)
    - Client sends: {"type": "cancel"} (barge-in)
    - Server sends: {"type": "audio", "data": "<base64 PCM16 audio>"}
    - Server sends: {"type": "transcription", "text": "...", "status": "listening|processing|complete"}
    - Server sends: {"type": "avatar_speaking", "duration_ms": int, "visemes": [...]}
    - Server sends: {"type": "avatar_session", "webrtc_config": {...}} (on connect)
    - Server sends: {"type": "error", "message": "..."}
    """
    await websocket.accept()

    logger.info(f"VoiceLive WebSocket connected: {session_id}")

    try:
        from backend.voice.voicelive_service import voicelive_service
        from backend.voice import create_avatar_session, avatar_service

        # Default to Elena, but allow agent selection via WebSocket message
        current_agent_id = "elena"

        # Create avatar session for this voice session
        avatar_session = await create_avatar_session(session_id, current_agent_id)

        # Send avatar session configuration to frontend
        await websocket.send_json(
            {
                "type": "avatar_session",
                "session_id": avatar_session.session_id,
                "agent_id": avatar_session.agent_id,
                "webrtc_config": avatar_service.get_webrtc_config(avatar_session),
            }
        )

        # Create VoiceLive session
        session = await voicelive_service.create_session(
            session_id=session_id,
            agent_id=current_agent_id,
        )

        # Track response state for avatar
        response_start_time = None
        response_text = ""
        response_visemes = []
        active_response = False
        response_api_done = False

        # Event handlers
        async def on_audio(audio_data: bytes):
            """Handle audio from assistant"""
            nonlocal response_start_time

            if response_start_time is None:
                response_start_time = time.time()
                # Notify avatar that speaking is starting
                await websocket.send_json(
                    {
                        "type": "avatar_speaking",
                        "status": "start",
                        "agent_id": current_agent_id,
                    }
                )

            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            await websocket.send_json(
                {
                    "type": "audio",
                    "data": audio_base64,
                    "format": "pcm16",
                }
            )

        async def on_transcription(status: str, text: str = ""):
            """Handle transcription updates"""
            nonlocal response_text
            if text:
                response_text = text
            await websocket.send_json(
                {
                    "type": "transcription",
                    "status": status,
                    "text": text,
                }
            )

        async def on_response_created():
            """Handle response creation - avatar can prepare"""
            nonlocal active_response, response_api_done
            active_response = True
            response_api_done = False
            logger.debug("Response created - avatar can prepare")

        async def on_response_done():
            """Handle response completion for avatar"""
            nonlocal response_start_time, response_visemes, active_response, response_api_done
            response_api_done = True
            active_response = False

            if response_start_time:
                duration_ms = int((time.time() - response_start_time) * 1000)
                # Notify avatar that speaking is done
                await websocket.send_json(
                    {
                        "type": "avatar_speaking",
                        "status": "done",
                        "duration_ms": duration_ms,
                        "visemes": response_visemes,
                        "agent_id": current_agent_id,
                    }
                )
                response_start_time = None
                response_visemes = []

        async def on_conversation_item(event):
            """Handle conversation item events - may contain text for viseme generation"""
            # Conversation items may contain text that we can use for viseme generation
            # This is useful for avatar lip-sync
            if hasattr(event, "item") and hasattr(event.item, "content"):
                logger.debug(
                    f"Conversation item text: {event.item.content[:50] if event.item.content else 'N/A'}..."
                )
                # Could extract text here for viseme generation if needed

        # Start event processing in background
        event_task = asyncio.create_task(
            session.process_events(
                on_audio,
                on_transcription,
                on_response_done,
                on_response_created,
                on_conversation_item,
            )
        )

        try:
            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_json()
                except Exception as e:
                    logger.debug(f"WebSocket receive error (may be disconnect): {e}")
                    break

                msg_type = data.get("type")

                if msg_type == "agent":
                    # Switch agent (requires reconnecting with new agent)
                    new_agent_id = data.get("agent_id", "elena")
                    if new_agent_id != current_agent_id and new_agent_id in [
                        "elena",
                        "marcus",
                    ]:
                        logger.info(
                            f"Switching agent from {current_agent_id} to {new_agent_id}"
                        )
                        # Cancel current event processing first
                        event_task.cancel()
                        try:
                            await event_task
                        except asyncio.CancelledError:
                            pass
                        # Close current session
                        await voicelive_service.close_session(session_id)
                        # Create new session with different agent
                        current_agent_id = new_agent_id

                        # Update avatar session for new agent
                        from backend.voice import close_avatar_session

                        await close_avatar_session(session_id)
                        avatar_session = await create_avatar_session(
                            session_id, current_agent_id
                        )
                        await websocket.send_json(
                            {
                                "type": "avatar_session",
                                "session_id": avatar_session.session_id,
                                "agent_id": avatar_session.agent_id,
                                "webrtc_config": avatar_service.get_webrtc_config(
                                    avatar_session
                                ),
                            }
                        )

                        session = await voicelive_service.create_session(
                            session_id=session_id,
                            agent_id=current_agent_id,
                        )
                        # Restart event processing
                        event_task = asyncio.create_task(
                            session.process_events(
                                on_audio,
                                on_transcription,
                                on_response_done,
                                on_response_created,
                                on_conversation_item,
                            )
                        )
                        await websocket.send_json(
                            {
                                "type": "agent_switched",
                                "agent_id": current_agent_id,
                            }
                        )

                elif msg_type == "audio":
                    # Forward audio to VoiceLive
                    audio_data = data.get("data", "")
                    if audio_data:
                        try:
                            await session.send_audio(audio_data)
                        except Exception as e:
                            logger.error(f"Error sending audio to VoiceLive: {e}")
                            await websocket.send_json(
                                {
                                    "type": "error",
                                    "message": f"Failed to send audio: {str(e)}",
                                }
                            )

                elif msg_type == "text":
                    # Send text input (alternative to voice)
                    text = data.get("text", "")
                    if text and session.connection:
                        # VoiceLive supports text input via conversation API
                        # This would need to be implemented based on VoiceLive SDK
                        logger.info(f"Text input received: {text}")
                        await websocket.send_json(
                            {
                                "type": "info",
                                "message": "Text input not yet implemented for VoiceLive",
                            }
                        )

                elif msg_type == "cancel":
                    # Cancel current response (barge-in)
                    await session.cancel_response()

                elif msg_type == "close":
                    break

        finally:
            # Cleanup
            event_task.cancel()
            try:
                await event_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Error cancelling event task: {e}")

            await voicelive_service.close_session(session_id)
            # Close avatar session
            from backend.voice import close_avatar_session

            await close_avatar_session(session_id)
            logger.info(f"VoiceLive WebSocket disconnected: {session_id}")

    except WebSocketDisconnect:
        logger.info(f"VoiceLive WebSocket disconnected: {session_id}")
        await voicelive_service.close_session(session_id)
        # Close avatar session
        from backend.voice import close_avatar_session

        await close_avatar_session(session_id)
    except Exception as e:
        logger.error(f"VoiceLive WebSocket error: {e}")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": str(e),
                }
            )
        except Exception:
            pass
        await voicelive_service.close_session(session_id)


# =============================================================================
# DEPRECATED: Legacy Speech Services WebSocket Endpoint
# =============================================================================
# This endpoint is DEPRECATED and will be removed in a future version.
# Please use /api/v1/voice/voicelive/{session_id} instead.
# =============================================================================


@router.websocket("/ws/{session_id}")
async def voice_chat_websocket(websocket: WebSocket, session_id: str):
    """
    [DEPRECATED] Legacy WebSocket endpoint for real-time voice chat.

    This endpoint uses Speech Services (STT/TTS) and is being phased out.
    Please use /api/v1/voice/voicelive/{session_id} instead, which provides:
    - VoiceLive real-time voice conversation
    - Integrated avatar support
    - Better performance and lower latency

    This endpoint will be removed in a future version.
    """
    await websocket.accept()

    # Send deprecation warning
    await websocket.send_json(
        {
            "type": "warning",
            "message": "This endpoint is deprecated. Please use /api/v1/voice/voicelive/{session_id} instead.",
        }
    )

    logger.warning(
        f"DEPRECATED: Legacy voice WebSocket connected: {session_id} - Use VoiceLive endpoint instead"
    )

    try:
        from backend.voice import (
            create_avatar_session,
            get_voice_for_agent,
            recognize_speech,
            synthesize_speech,
        )
        from backend.agents import chat as agent_chat
        from backend.core import EnterpriseContext, Role, SecurityContext

        # Create avatar session
        await create_avatar_session(session_id, "elena")

        # Create context for agent
        security = SecurityContext(
            user_id="voice-user",
            tenant_id="voice-tenant",
            roles=[Role.ANALYST],
            scopes=["*"],
        )
        context = EnterpriseContext(security=security)
        context.episodic.conversation_id = session_id

        current_agent = "elena"
        audio_buffer = b""

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "audio":
                # Receive audio chunk
                audio_base64 = data.get("data", "")
                audio_chunk = base64.b64decode(audio_base64)
                audio_buffer += audio_chunk

            elif msg_type == "start_listening":
                audio_buffer = b""
                await websocket.send_json({"type": "status", "status": "listening"})

            elif msg_type == "stop_listening":
                if audio_buffer:
                    # Transcribe
                    result = await recognize_speech(audio_buffer)

                    await websocket.send_json(
                        {
                            "type": "transcription",
                            "text": result.text,
                            "is_final": True,
                            "confidence": result.confidence,
                        }
                    )

                    if result.text:
                        # Get agent response
                        response_text, context, agent_id = await agent_chat(
                            query=result.text, context=context, agent_id=current_agent
                        )

                        # Synthesize response
                        voice_id = get_voice_for_agent(agent_id)
                        synth_result = await synthesize_speech(
                            text=response_text, voice_id=voice_id, include_visemes=True
                        )

                        # Send response
                        await websocket.send_json(
                            {
                                "type": "response",
                                "text": response_text,
                                "agent_id": agent_id,
                                "audio": (
                                    base64.b64encode(synth_result.audio_data).decode()
                                    if synth_result.audio_data
                                    else ""
                                ),
                                "audio_format": synth_result.audio_format,
                                "duration_ms": synth_result.duration_ms,
                                "visemes": synth_result.visemes,
                            }
                        )

                        # Notify avatar speaking
                        await websocket.send_json(
                            {
                                "type": "avatar_speaking",
                                "duration_ms": synth_result.duration_ms,
                            }
                        )

                audio_buffer = b""

            elif msg_type == "switch_agent":
                current_agent = data.get("agent_id", "elena")
                await websocket.send_json(
                    {"type": "agent_switched", "agent_id": current_agent}
                )

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"Voice WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# =============================================================================
# Voice Configuration Endpoints
# =============================================================================


class VoiceConfigResponse(BaseModel):
    voices: list[dict]
    default_voice: str


@router.get("/config", response_model=VoiceConfigResponse)
async def get_voice_config(user: SecurityContext = Depends(get_current_user)):
    """Get available voice configurations"""
    from backend.voice import VOICE_CONFIG, VoiceId

    voices = [
        {
            "id": voice_id.value,
            "name": config["name"],
            "style": config["style"],
            "agent": "Elena" if voice_id == VoiceId.ELENA else "Marcus",
        }
        for voice_id, config in VOICE_CONFIG.items()
    ]

    return VoiceConfigResponse(voices=voices, default_voice=VoiceId.ELENA.value)


class AvatarConfigResponse(BaseModel):
    avatars: list[dict]


@router.get("/avatar/config", response_model=AvatarConfigResponse)
async def get_avatar_config(user: SecurityContext = Depends(get_current_user)):
    """Get available avatar configurations"""
    from backend.voice import AVATAR_CONFIG

    avatars = [
        {
            "agent_id": agent_id,
            "avatar_id": config.avatar_id,
            "style": config.style.value,
            "voice_name": config.voice_name,
            "background_color": config.background_color,
        }
        for agent_id, config in AVATAR_CONFIG.items()
    ]

    return AvatarConfigResponse(avatars=avatars)
