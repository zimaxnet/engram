"""
Voice Router

Provides voice endpoints with chat-based fallback:
- WebSocket endpoint for voice interaction using agents
- REST endpoints for voice configuration

Note: When VoiceLive realtime endpoint is not available, uses chat completions
with the agent system for text responses.

VoiceLive v2: Adds /realtime/token endpoint for browser-direct WebRTC connections.
"""

import asyncio
import base64
import json
import logging
import os
from typing import Optional, Any

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from backend.voice.voicelive_service import voicelive_service
from backend.core import get_settings, EnterpriseContext, SecurityContext, Role, MessageRole, Turn
from backend.agents import chat as agent_chat, get_agent
from backend.memory import memory_client, persist_conversation
from backend.api.middleware.auth import get_auth, get_current_user
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter()

# Timeouts for memory operations (seconds) - keep VoiceLive real-time loop responsive
VOICE_MEMORY_TIMEOUT = 2.0
VOICE_PERSIST_TIMEOUT = 10.0


def validate_voicelive_endpoint(endpoint: str) -> tuple[bool, str]:
    """
    Validate and detect VoiceLive endpoint type.
    
    Returns:
        (is_valid, endpoint_type) where endpoint_type is:
        - "unified" for services.ai.azure.com endpoints
        - "direct" for openai.azure.com endpoints
        - "invalid" if endpoint format is unrecognized
    """
    if not endpoint:
        return False, "invalid"
    
    endpoint_lower = endpoint.lower().rstrip('/')
    
    if "services.ai.azure.com" in endpoint_lower:
        return True, "unified"
    elif "openai.azure.com" in endpoint_lower:
        return True, "direct"
    else:
        return False, "invalid"


def get_endpoint_type(endpoint: str) -> str:
    """Get the endpoint type (unified or direct) for logging/validation."""
    _, endpoint_type = validate_voicelive_endpoint(endpoint)
    return endpoint_type


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
    # Authentication: Extract JWT token from query parameter since WebSockets
    # cannot send Authorization headers. Validate token and extract user identity.
    # ---------------------------------------------------------------------
    settings = get_settings()
    
    # Extract token from query parameter
    token_param = websocket.query_params.get("token")
    
    # Determine user_id based on auth requirements
    if settings.auth_required:
        if not token_param:
            logger.warning(f"VoiceLive WebSocket: Authentication required but no token provided for session {session_id}")
            await websocket.close(code=1008, reason="Authentication required")
            return
        
        # Validate token
        try:
            auth = get_auth()
            token = await auth.validate_token(token_param)
            user_id = token.oid
            tenant_id = token.tid
            email = token.email
            display_name = token.name
            roles = auth.map_roles(token.roles)
            scopes = auth.extract_scopes(token)
            logger.info(f"VoiceLive WebSocket: Authenticated user {user_id} for session {session_id}")
        except Exception as e:
            logger.warning(f"VoiceLive WebSocket: Token validation failed for session {session_id}: {e}")
            await websocket.close(code=1008, reason="Invalid token")
            return
    else:
        # POC mode: use default user when auth not required
        user_id = "poc-user"
        tenant_id = settings.azure_tenant_id or "poc-tenant"
        email = None
        display_name = None
        roles = [Role.ADMIN]
        scopes = ["*"]
        logger.info(f"VoiceLive WebSocket: Using POC user for session {session_id} (AUTH_REQUIRED=false)")
    
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

    voice_context = EnterpriseContext(security=security, context_version="1.0.0")
    voice_context.episodic.conversation_id = session_id
    session["context"] = voice_context

    async def _ensure_memory_session():
        user_id_log = security.user_id  # Capture user_id for logging
        logger.info(f"Background task started: ensuring memory session for user: {user_id_log}")
        try:
            # Build session metadata with full user identity information
            # This ensures consistent user identity and project/department boundaries
            session_metadata = {
                "tenant_id": security.tenant_id,
                "channel": "voice",
                "agent_id": session.get("agent_id", "elena"),
            }
            # Include user identity metadata for proper attribution
            if security.email:
                session_metadata["email"] = security.email
            if security.display_name:
                session_metadata["display_name"] = security.display_name
            
            await asyncio.wait_for(
                memory_client.get_or_create_session(
                    session_id=session_id,
                    user_id=user_id_log,
                    metadata=session_metadata,
                ),
                timeout=VOICE_MEMORY_TIMEOUT,
            )
            logger.info(f"Background task completed: memory session ensured for user: {user_id_log}")
        except asyncio.TimeoutError:
            logger.warning(f"Voice memory session init timed out for user: {user_id_log}")
        except Exception as e:
            logger.warning(f"Voice memory session init failed for user: {user_id_log}: {e}")

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
        
        # Check if avatar should be enabled (for Elena)
        enable_avatar = session["agent_id"] == "elena"
        
        # Get agent configuration
        agent_config = session["voice_config"]
        
        # ---------------------------------------------------------------------
        # CRITICAL: Ensure user exists in Zep before creating session
        # ---------------------------------------------------------------------
        try:
            await memory_client.get_or_create_user(
                user_id=security.user_id,
                metadata={
                    "tenant_id": security.tenant_id,
                    "email": security.email,
                    "display_name": security.display_name,
                }
            )
            logger.info(f"Ensured user exists in Zep: {security.user_id}")
        except Exception as e:
            logger.warning(f"Failed to ensure user {security.user_id} exists in Zep: {e}. Voice session may fail.")
        
        # ---------------------------------------------------------------------
        # Enrichment: Fetch user context (facts) from Zep to personalize the session.
        # We do this once at session start to avoid latency during the call.
        # ---------------------------------------------------------------------
        enriched_instructions = agent_config.instructions
        try:
            logger.info(f"Enriching voice session for user: {security.user_id}")
            facts = await asyncio.wait_for(
                memory_client.get_facts(user_id=security.user_id, limit=20),
                timeout=VOICE_MEMORY_TIMEOUT
            )
            if facts:
                # Populate EnterpriseContext semantic layer
                for fact in facts:
                    # Map Zep Fact/Node to GraphNode if needed, or if get_facts returns GraphNode compatible objects
                    # Assuming memory_client.get_facts returns list of objects with 'content', 'uuid', etc.
                    # We might need to adapter them if they aren't exactly GraphNodes, but for now we trust the attribute access.
                    voice_context.semantic.add_fact(fact)
                
                # Use the context object to generate the summary string
                context_summary = voice_context.semantic.get_context_summary()
                
                enriched_instructions += f"\n\n## User Context (from Memory)\nThe following facts about the user are available context. Use them to personalize the conversation naturally, but do not recite them unless asked:\n{context_summary}"
                logger.info(f"Injected {len(facts)} facts into voice instructions via EnterpriseContext")
            else:
                logger.info("No facts found for enrichment")
        except asyncio.TimeoutError:
            logger.warning("Voice enrichment timed out - proceeding without context")
        except Exception as e:
            logger.warning(f"Voice enrichment failed: {e}")

        # Get VoiceLive credential
        credential = voicelive_service.get_credential()
        
        # Connect to VoiceLive
        async with connect(
            endpoint=voicelive_service.endpoint,
            credential=credential,
            model=voicelive_service.model,
        ) as voicelive_connection:
            
            # Configure session with avatar support for Elena
            modalities = [Modality.TEXT, Modality.AUDIO]
            session_kwargs = {
                "instructions": enriched_instructions,
                "input_audio_format": InputAudioFormat.PCM16,
                "output_audio_format": OutputAudioFormat.PCM16,
                "voice": AzureStandardVoice(name=agent_config.voice_name),
                "turn_detection": ServerVad(
                    threshold=0.6,
                    prefix_padding_ms=300,
                    silence_duration_ms=800,
                ),
            }
            
            # Video routing: Direct to browser (not through backend)
            # Audio and transcripts: Through backend for memory persistence
            avatar_enabled = False
            video_direct_url = None
            if enable_avatar:
                logger.info(f"📹 Video will be routed directly to browser (bypassing backend)")
                logger.info(f"   Audio and transcripts will continue through backend for memory persistence")
                # Don't add VIDEO modality to backend connection - browser will connect directly
                # Instead, we'll provide a token for direct video connection
                avatar_enabled = True  # Mark as enabled so we can provide video connection info
            
            session_config = RequestSession(
                modalities=modalities,
                **session_kwargs
            )
            
            # Log session configuration details for debugging
            logger.info(f"📋 Session configuration:")
            logger.info(f"   Modalities: {[str(m) for m in modalities]}")
            logger.info(f"   Avatar enabled: {avatar_enabled}")
            if avatar_enabled and "avatar" in session_kwargs:
                logger.info(f"   Avatar config: {session_kwargs['avatar']}")
            logger.info(f"   Voice: {session_kwargs.get('voice', 'N/A')}")
            logger.info(f"   Instructions length: {len(session_kwargs.get('instructions', ''))}")
            
            # Try to update session, fallback to audio-only if avatar fails
            try:
                logger.info("🔄 Attempting to update VoiceLive session with current configuration...")
                await voicelive_connection.session.update(session=session_config)
                logger.info(f"✅ VoiceLive session updated successfully (avatar={'enabled' if avatar_enabled else 'disabled'})")
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"❌ Session update failed:")
                logger.error(f"   Error type: {error_type}")
                logger.error(f"   Error message: {error_msg}")
                logger.error(f"   Full exception:", exc_info=True)
                
                # Check if this is an HTTP error with response details
                if hasattr(e, 'response'):
                    try:
                        response_text = getattr(e.response, 'text', 'N/A')
                        status_code = getattr(e.response, 'status_code', 'N/A')
                        logger.error(f"   HTTP Status: {status_code}")
                        logger.error(f"   Response: {response_text[:500]}")  # First 500 chars
                    except:
                        pass
                
                if avatar_enabled and Modality.VIDEO in modalities:
                    logger.warning(f"⚠️  Session update with avatar failed, retrying without VIDEO modality...")
                    # Retry without VIDEO modality
                    modalities.remove(Modality.VIDEO)
                    if "avatar" in session_kwargs:
                        del session_kwargs["avatar"]
                    session_config = RequestSession(
                        modalities=modalities,
                        **session_kwargs
                    )
                    logger.info(f"🔄 Retrying with audio-only configuration (modalities: {[str(m) for m in modalities]})")
                    try:
                        await voicelive_connection.session.update(session=session_config)
                        logger.info("✅ VoiceLive session updated successfully (audio-only fallback)")
                        avatar_enabled = False
                    except Exception as retry_error:
                        # If retry also fails, log but don't fail the connection - continue with audio
                        logger.error(f"❌ Session update failed even without VIDEO modality:")
                        logger.error(f"   Error type: {type(retry_error).__name__}")
                        logger.error(f"   Error message: {str(retry_error)}")
                        logger.error(f"   Full exception:", exc_info=True)
                        if hasattr(retry_error, 'response'):
                            try:
                                response_text = getattr(retry_error.response, 'text', 'N/A')
                                status_code = getattr(retry_error.response, 'status_code', 'N/A')
                                logger.error(f"   HTTP Status: {status_code}")
                                logger.error(f"   Response: {response_text[:500]}")
                            except:
                                pass
                        logger.warning("   Continuing with existing session configuration (audio-only)")
                        avatar_enabled = False
                        # Don't raise - allow connection to continue with whatever session state exists
                else:
                    # If avatar wasn't enabled or VIDEO not in modalities, this is a real error
                    logger.error(f"❌ VoiceLive session update failed (non-avatar error)")
                    raise
            
            # Send ready message with video connection info if avatar is enabled
            ready_message = {
                "type": "agent_switched",
                "agent_id": session["agent_id"],
            }
            
            # If avatar is enabled, provide video connection token for direct browser connection
            # NOTE: Video token generation is optional - if it fails, audio still works
            # We use asyncio.create_task to make it non-blocking so failures don't break connection
            if avatar_enabled:
                async def _generate_video_token_safely():
                    """Generate video token in background - failures don't affect connection."""
                    try:
                        # Generate token for direct video connection
                        # Use failsafe token generation for video
                        video_session_config = {
                            "model": voicelive_service.model,
                            "modalities": ["video", "text"],
                            "instructions": agent_config.instructions,
                            "voice": agent_config.voice_name,
                        }
                        
                        # Add avatar config if available
                        if "avatar" in session_kwargs:
                            video_session_config["avatar"] = session_kwargs["avatar"]
                        
                        # Determine endpoint type
                        endpoint_for_video = voicelive_service.endpoint.rstrip('/')
                        is_valid, endpoint_type_video = validate_voicelive_endpoint(endpoint_for_video)
                        
                        # For browser video connections, prefer API key over Managed Identity token
                        # because browser WebSocket cannot set Authorization headers
                        # We'll try API key first, then fall back to Managed Identity
                        video_token_response = await _generate_token_with_failsafe_for_browser(
                            endpoint=endpoint_for_video,
                            endpoint_type=endpoint_type_video if is_valid else "unified",
                            project_name=voicelive_service.project_name,
                            api_version=voicelive_service.api_version,
                            model=voicelive_service.model,
                            session_config=video_session_config,
                            voicelive_service=voicelive_service,
                        )
                        
                        if not video_token_response:
                            raise Exception("All failsafe token generation strategies failed for video")
                        
                        # Send video connection info to client (if still connected)
                        try:
                            await websocket.send_json({
                                "type": "video_connection_ready",
                                "video_connection": {
                                    "token": video_token_response.token,
                                    "endpoint": video_token_response.endpoint,
                                    "modalities": ["video", "text"],
                                }
                            })
                            logger.info(f"📹 Video connection token provided for direct browser connection")
                            logger.info(f"   Endpoint: {video_token_response.endpoint}")
                        except Exception as send_error:
                            logger.warning(f"⚠️  Failed to send video connection info: {send_error}")
                    except HTTPException as e:
                        # HTTPException from get_realtime_token - log but don't fail connection
                        logger.warning(f"⚠️  Video token generation failed (HTTP {e.status_code}): {e.detail}")
                        logger.warning(f"   Video will not be available, but audio will work")
                    except Exception as e:
                        # Any other exception - log but don't fail connection
                        error_msg = str(e)
                        logger.warning(f"⚠️  Failed to generate video connection token: {error_msg}")
                        logger.warning(f"   Error type: {type(e).__name__}")
                        logger.warning(f"   Video will not be available, but audio will work")
                        # Don't log full traceback for video token failures - they're expected with unified endpoints
                
                # Start video token generation in background (non-blocking)
                asyncio.create_task(_generate_video_token_safely())
                logger.info(f"📹 Video token generation started in background (non-blocking)")
            
            await websocket.send_json(ready_message)
            
            # Create task to process VoiceLive events
            async def process_voicelive_events():
                # Track avatar support status for event handling
                nonlocal avatar_enabled
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
                    # Extract user_id explicitly for logging and validation
                    user_id = voice_context.security.user_id
                    logger.info(f"Background task started: persisting voice conversation for user: {user_id}")
                    try:
                        await asyncio.wait_for(
                            persist_conversation(voice_context),
                            timeout=VOICE_PERSIST_TIMEOUT,
                        )
                        logger.info(f"Background task completed: voice conversation persisted for user: {user_id}")
                    except asyncio.TimeoutError:
                        logger.warning(f"Voice memory persistence timed out (background) for user: {user_id}")
                    except Exception as e:
                        logger.warning(f"Voice memory persistence failed (background) for user: {user_id}: {e}")

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
                        
                        # Video events are NOT handled here - video goes directly to browser
                        # Skip any video events that might come through (shouldn't happen without VIDEO modality)
                        # This keeps the backend focused on audio and transcripts only
                        
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
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Log full error details for debugging
        logger.error(f"❌ VoiceLive connection error (outer handler):")
        logger.error(f"   Error type: {error_type}")
        logger.error(f"   Error message: {error_msg}")
        logger.error(f"   Full exception:", exc_info=True)
        
        # Check if this is an HTTP error with response details
        if hasattr(e, 'response'):
            try:
                response_text = getattr(e.response, 'text', 'N/A')
                status_code = getattr(e.response, 'status_code', 'N/A')
                logger.error(f"   HTTP Status: {status_code}")
                logger.error(f"   Response: {response_text[:1000]}")  # First 1000 chars
            except:
                pass
        
        # Don't expose VIDEO modality errors to user - we've already handled fallback
        # Check for video-related errors (token generation, modality, etc.)
        is_video_error = (
            "VIDEO" in error_msg.upper() or 
            "avatar" in error_msg.lower() or 
            "video.*token" in error_msg.lower() or
            "realtime/token" in error_msg or
            "get_realtime_token" in error_msg or
            "client_secrets" in error_msg
        )
        
        if is_video_error:
            logger.warning(f"⚠️  Avatar/video-related error (handled gracefully, user will see audio-only mode)")
            logger.warning(f"   Original error: {error_msg[:200]}")
            # Send a user-friendly message instead of technical error
            await websocket.send_json({
                "type": "error",
                "message": "Voice connection established (audio-only mode). Avatar video is not available.",
            })
        else:
            logger.error(f"❌ Non-avatar connection error - this is a real failure")
            await websocket.send_json({
                "type": "error",
                "message": f"Voice connection failed: {error_msg}",
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
            "sage": {
                "voice": voicelive_service.get_agent_voice_config("sage").voice_name,
            },
        },
    }


# -----------------------------------------------------------------------------
# VoiceLive v2: Ephemeral Token Endpoint for Browser-Direct WebRTC
# -----------------------------------------------------------------------------

async def _generate_token_with_failsafe_for_browser(
    endpoint: str,
    endpoint_type: str,
    project_name: Optional[str],
    api_version: str,
    model: str,
    session_config: dict,
    voicelive_service: Any,
) -> Optional[TokenResponse]:
    """
    Failsafe token generation optimized for browser connections.
    
    Browser WebSocket cannot set Authorization headers, so we prefer API key
    over Managed Identity tokens (which require Bearer header).
    
    Strategy order:
    1. API key with current API version (preferred for browser)
    2. API key with fallback API versions
    3. Managed Identity with current API version (fallback - may not work in browser)
    4. Managed Identity with fallback API versions
    
    Returns TokenResponse if successful, None if all strategies fail.
    """
    from azure.identity import DefaultAzureCredential
    from azure.core.credentials import AzureKeyCredential
    import httpx
    
    logger.info("🔄 Starting failsafe token generation (browser-optimized)...")
    
    # Get credential
    credential = voicelive_service.get_credential()
    
    # Build WebSocket URL helper
    ws_base = endpoint.replace("https://", "wss://").replace("http://", "ws://")
    
    def build_ws_url(version: str) -> str:
        """Build WebSocket URL for given API version."""
        if endpoint_type == "direct":
            return f"{ws_base}/openai/realtime?api-version={version}&deployment={model}"
        elif project_name:
            return f"{ws_base}/api/projects/{project_name}/voice-live/realtime?api-version={version}&model={model}"
        else:
            return f"{ws_base}/voice-live/realtime?api-version={version}&model={model}"
    
    # Strategy 1: Try API key first (preferred for browser - can use as query parameter)
    # Check voicelive_service.key first (from settings), then environment, then credential
    api_key = voicelive_service.key or os.getenv("AZURE_VOICELIVE_KEY", "")
    if not api_key and isinstance(credential, AzureKeyCredential):
        api_key = credential.key
    
    if api_key:
        logger.info(f"📋 Strategy 1 (Browser): API key with API version {api_version}")
        try:
            # For unified endpoints, API key can be used directly in WebSocket query parameter
            logger.info("✅ Strategy 1 succeeded: Using API key for browser WebSocket authentication")
            return TokenResponse(
                token=api_key,  # Browser will use this as api-key query parameter
                endpoint=build_ws_url(api_version),
                expires_at=None,
            )
        except Exception as e:
            logger.warning(f"⚠️  Strategy 1 failed: {str(e)[:100]}")
    
    # Strategy 2: Try API key with fallback API versions
    if api_key:
        fallback_versions = ["2024-10-01-preview", "2024-08-01-preview", "2024-05-01-preview"]
        for fallback_version in fallback_versions:
            if fallback_version == api_version:
                continue
            logger.info(f"📋 Strategy 2 (Browser): API key with fallback API version {fallback_version}")
            try:
                logger.info(f"✅ Strategy 2 succeeded: API key with API version {fallback_version}")
                return TokenResponse(
                    token=api_key,
                    endpoint=build_ws_url(fallback_version),
                    expires_at=None,
                )
            except Exception as e:
                logger.warning(f"⚠️  Strategy 2 (API {fallback_version}) failed: {str(e)[:100]}")
                continue
    
    # Strategy 3: Fallback to Managed Identity (may not work in browser due to header requirement)
    if isinstance(credential, DefaultAzureCredential):
        logger.info(f"📋 Strategy 3 (Browser Fallback): Managed Identity with API version {api_version}")
        logger.warning("⚠️  Managed Identity tokens require Authorization header - browser WebSocket may fail")
        try:
            token = credential.get_token("https://ai.azure.com/.default").token
            logger.info("✅ Strategy 3 succeeded: Managed Identity token obtained (may not work in browser)")
            return TokenResponse(
                token=token,
                endpoint=build_ws_url(api_version),
                expires_at=None,
            )
        except Exception as e:
            logger.warning(f"⚠️  Strategy 3 failed: {str(e)[:100]}")
    
    logger.warning("❌ All browser-optimized token generation strategies failed.")
    return None

class TokenRequest(BaseModel):
    """Request body for realtime token endpoint"""
    agent_id: str = "elena"
    session_id: Optional[str] = None
    modalities: Optional[list[str]] = None  # Optional: defaults to ["audio", "text"], can be ["video", "text"] for video-only


class TokenResponse(BaseModel):
    """Ephemeral token response for WebRTC connection"""
    token: str
    endpoint: str
    expires_at: Optional[str] = None


async def _generate_token_with_failsafe(
    endpoint: str,
    endpoint_type: str,
    project_name: Optional[str],
    api_version: str,
    model: str,
    session_config: dict,
    voicelive_service: Any,
) -> Optional[TokenResponse]:
    """
    Failsafe token generation with multiple fallback strategies.
    
    Strategy order:
    1. Managed Identity with current API version
    2. Managed Identity with fallback API versions
    3. API key with current API version (direct WebSocket for unified endpoints)
    4. REST token endpoint for direct endpoints with current API version
    5. REST token endpoint with fallback API versions
    
    Returns TokenResponse if successful, None if all strategies fail.
    """
    from azure.identity import DefaultAzureCredential
    from azure.core.credentials import AzureKeyCredential
    import httpx
    
    logger.info("🔄 Starting failsafe token generation...")
    
    # Get credential
    credential = voicelive_service.get_credential()
    
    # Build WebSocket URL helper
    ws_base = endpoint.replace("https://", "wss://").replace("http://", "ws://")
    
    def build_ws_url(version: str) -> str:
        """Build WebSocket URL for given API version."""
        if endpoint_type == "direct":
            return f"{ws_base}/openai/realtime?api-version={version}&deployment={model}"
        elif project_name:
            return f"{ws_base}/api/projects/{project_name}/voice-live/realtime?api-version={version}&model={model}"
        else:
            return f"{ws_base}/voice-live/realtime?api-version={version}&model={model}"
    
    # Strategy 1: Try Managed Identity with current API version
    if isinstance(credential, DefaultAzureCredential):
        logger.info(f"📋 Strategy 1: Managed Identity with API version {api_version}")
        try:
            token = credential.get_token("https://ai.azure.com/.default").token
            logger.info("✅ Strategy 1 succeeded: Managed Identity token obtained")
            return TokenResponse(
                token=token,
                endpoint=build_ws_url(api_version),
                expires_at=None,
            )
        except Exception as e:
            logger.warning(f"⚠️  Strategy 1 failed: {str(e)[:100]}")
    
    # Strategy 2: Try Managed Identity with fallback API versions
    if isinstance(credential, DefaultAzureCredential):
        fallback_versions = ["2024-10-01-preview", "2024-08-01-preview", "2024-05-01-preview"]
        for fallback_version in fallback_versions:
            if fallback_version == api_version:
                continue  # Skip if already tried
            logger.info(f"📋 Strategy 2: Managed Identity with API version {fallback_version}")
            try:
                token = credential.get_token("https://ai.azure.com/.default").token
                logger.info(f"✅ Strategy 2 succeeded: Managed Identity token with API version {fallback_version}")
                return TokenResponse(
                    token=token,
                    endpoint=build_ws_url(fallback_version),
                    expires_at=None,
                )
            except Exception as e:
                logger.warning(f"⚠️  Strategy 2 (API {fallback_version}) failed: {str(e)[:100]}")
                continue
    
    # Strategy 3: Try API key with current API version (for unified endpoints, use direct WebSocket)
    api_key = os.getenv("AZURE_VOICELIVE_KEY", "")
    if not api_key and isinstance(credential, AzureKeyCredential):
        api_key = credential.key
    
    if api_key:
        logger.info(f"📋 Strategy 3: API key with current API version")
        try:
            # For unified endpoints, API key can be used directly in WebSocket header
            logger.info("✅ Strategy 3 succeeded: Using API key for WebSocket authentication")
            return TokenResponse(
                token=api_key,  # Browser will use this as api-key header
                endpoint=build_ws_url(api_version),
                expires_at=None,
            )
        except Exception as e:
            logger.warning(f"⚠️  Strategy 3 failed: {str(e)[:100]}")
    
    # Strategy 4: Try REST endpoint for direct endpoints (if not unified)
    if endpoint_type == "direct" and api_key:
        logger.info(f"📋 Strategy 4: REST token endpoint for direct endpoint with API version {api_version}")
        try:
            token_url = f"{endpoint}/openai/deployments/{model}/realtime/client_secrets"
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Content-Type": "application/json",
                    "api-key": api_key,
                }
                response = await client.post(
                    token_url,
                    headers=headers,
                    params={"api-version": api_version},
                    json=session_config,
                )
                if response.status_code == 200:
                    data = response.json()
                    ephemeral_token = data.get("value", "")
                    if ephemeral_token:
                        logger.info("✅ Strategy 4 succeeded: REST token endpoint")
                        return TokenResponse(
                            token=ephemeral_token,
                            endpoint=build_ws_url(api_version),
                            expires_at=data.get("expires_at"),
                        )
        except Exception as e:
            logger.warning(f"⚠️  Strategy 4 failed: {str(e)[:100]}")
    
    # Strategy 5: Try REST endpoint with fallback API versions (for direct endpoints)
    if endpoint_type == "direct" and api_key:
        fallback_versions = ["2024-10-01-preview", "2024-08-01-preview"]
        for fallback_version in fallback_versions:
            if fallback_version == api_version:
                continue
            logger.info(f"📋 Strategy 5: REST token endpoint with API version {fallback_version}")
            try:
                token_url = f"{endpoint}/openai/deployments/{model}/realtime/client_secrets"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {
                        "Content-Type": "application/json",
                        "api-key": api_key,
                    }
                    response = await client.post(
                        token_url,
                        headers=headers,
                        params={"api-version": fallback_version},
                        json=session_config,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        ephemeral_token = data.get("value", "")
                        if ephemeral_token:
                            logger.info(f"✅ Strategy 5 succeeded: REST token with API version {fallback_version}")
                            return TokenResponse(
                                token=ephemeral_token,
                                endpoint=build_ws_url(fallback_version),
                                expires_at=data.get("expires_at"),
                            )
            except Exception as e:
                logger.warning(f"⚠️  Strategy 5 (API {fallback_version}) failed: {str(e)[:100]}")
                continue
    
    # All strategies failed
    logger.warning("❌ All token generation strategies failed")
    return None


@router.post("/realtime/token", response_model=TokenResponse)
async def get_realtime_token(request: TokenRequest):
    """
    Generate an ephemeral token for direct browser-to-Azure WebRTC connection.
    
    The browser calls this endpoint to get a short-lived token, then uses it
    to establish a direct WebRTC connection to Azure's Realtime API.
    
    This is VoiceLive v2 architecture — audio flows directly browser↔Azure,
    bypassing the backend for lower latency.
    """
    # Validate VoiceLive is configured
    if not voicelive_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="VoiceLive not configured. Set AZURE_VOICELIVE_ENDPOINT and AZURE_VOICELIVE_KEY."
        )
    
    # Validate endpoint format
    endpoint = voicelive_service.endpoint.rstrip('/')
    is_valid, endpoint_type = validate_voicelive_endpoint(endpoint)
    if not is_valid:
        logger.error(f"Invalid VoiceLive endpoint format: {endpoint}")
        raise HTTPException(
            status_code=503,
            detail=f"Invalid VoiceLive endpoint format. Expected 'services.ai.azure.com' or 'openai.azure.com', got: {endpoint}"
        )
    
    logger.info(f"Using {endpoint_type} endpoint: {endpoint}")
    
    # Get agent configuration
    agent_config = voicelive_service.get_agent_voice_config(request.agent_id)
    
    # Build session configuration for the ephemeral token
    # Note: Body must be flattened (not nested under "session") per Azure Realtime API spec
    # Support both audio-only (backend proxy) and video-only (direct browser) connections
    modalities = request.modalities if request.modalities else ["audio", "text"]
    
    session_config = {
        "model": voicelive_service.model,
        "modalities": modalities,
        "instructions": agent_config.instructions,
        "voice": agent_config.voice_name,
    }
    
    # Add audio-specific config only if audio is in modalities
    if "audio" in modalities:
        session_config["input_audio_transcription"] = {
            "model": "whisper-1"  # Enable input transcription
        }
        session_config["turn_detection"] = {
            "type": "server_vad",
            "threshold": 0.6,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 800,
        }
    
    # Add video/avatar config if video is in modalities
    if "video" in modalities and request.agent_id == "elena":
        session_config["avatar"] = {
            "avatar_id": "en-US-JennyNeural",  # Match Elena's voice
            "style": "professional",
            "emotion": "neutral",
            "resolution": "1080p",
            "background": "transparent",
        }
        logger.info(f"📹 Video/avatar configuration added for direct browser connection")
    
    # Validate required fields
    required_fields = ["model", "modalities", "instructions", "voice"]
    missing_fields = [field for field in required_fields if field not in session_config or not session_config[field]]
    if missing_fields:
        logger.error(f"Missing required fields in session config: {missing_fields}")
        raise HTTPException(
            status_code=500,
            detail=f"Invalid session configuration: missing required fields {missing_fields}"
        )
    
    # Validate modalities
    if not isinstance(session_config["modalities"], list) or not session_config["modalities"]:
        raise HTTPException(
            status_code=500,
            detail="modalities must be a non-empty list"
        )
    
    # Determine endpoint type and construct token URL
    def build_token_url(endpoint: str, model: str, endpoint_type: str, project_name: Optional[str] = None) -> str:
        """
        Build the correct token URL based on endpoint type.
        
        For unified endpoints (services.ai.azure.com):
        - With project: /api/projects/{project}/openai/realtime/client_secrets
        - Without project: /openai/realtime/client_secrets
        
        For direct endpoints (openai.azure.com): 
        - /openai/deployments/{model}/realtime/client_secrets
        """
        if endpoint_type == "direct":
            # Direct OpenAI resource - Azure OpenAI requires deployment in path
            return f"{endpoint}/openai/deployments/{model}/realtime/client_secrets"
        else:
            # Unified endpoint (services.ai.azure.com)
            if project_name:
                # Project-based unified endpoint
                return f"{endpoint}/api/projects/{project_name}/openai/realtime/client_secrets"
            else:
                # Standard unified endpoint (no project)
                return f"{endpoint}/openai/realtime/client_secrets"
    
    # Get project name if configured (for project-based unified endpoints)
    project_name = voicelive_service.project_name
    api_version = voicelive_service.api_version
    
    token_url = build_token_url(endpoint, voicelive_service.model, endpoint_type, project_name)
    logger.info(f"Requesting ephemeral token from: {token_url}")
    logger.info(f"Using API version: {api_version}")
    if project_name:
        logger.info(f"Using project: {project_name}")
    logger.debug(f"Session config: {json.dumps(session_config, indent=2)}")
    
    try:
        # Use failsafe token generation with multiple fallback strategies
        token_response = await _generate_token_with_failsafe(
            endpoint=endpoint,
            endpoint_type=endpoint_type,
            project_name=project_name,
            api_version=api_version,
            model=voicelive_service.model,
            session_config=session_config,
            voicelive_service=voicelive_service,
        )
        
        if token_response:
            logger.info("✅ Token generated successfully using failsafe strategy")
            return token_response
        else:
            # All strategies failed - fall back to original logic
            logger.warning("⚠️  All failsafe strategies failed, falling back to original logic")
            # For unified endpoints (with or without project), the REST /client_secrets endpoint is not available.
            # Use direct WebSocket authentication instead (Managed Identity or API key).
            use_direct_websocket = endpoint_type == "unified"
        
        if use_direct_websocket:
            # For project-based unified endpoints, the REST /client_secrets endpoint is not available.
            # Instead, we use Managed Identity or API key directly for WebSocket authentication.
            logger.info("Using direct WebSocket authentication for project-based unified endpoint")
            
            # Get credential (Managed Identity preferred, fallback to API key)
            credential = voicelive_service.get_credential()
            
            # Construct WebSocket URL for unified endpoint
            ws_base = endpoint.replace("https://", "wss://").replace("http://", "ws://")
            if project_name:
                # Project-based unified endpoint
                # Format: wss://<endpoint>/api/projects/<project>/voice-live/realtime?api-version=<version>&model=<model>
                ws_url = f"{ws_base}/api/projects/{project_name}/voice-live/realtime?api-version={api_version}&model={voicelive_service.model}"
            else:
                # Standard unified endpoint (no project)
                # Format: wss://<endpoint>/voice-live/realtime?api-version=<version>&model=<model>
                ws_url = f"{ws_base}/voice-live/realtime?api-version={api_version}&model={voicelive_service.model}"
            
            logger.info(f"WebSocket URL for direct connection: {ws_url}")
            
            # Check credential type
            from azure.identity import DefaultAzureCredential
            from azure.core.credentials import AzureKeyCredential
            
            if isinstance(credential, DefaultAzureCredential):
                # Use Managed Identity - get token for WebSocket authentication
                try:
                    token = credential.get_token("https://ai.azure.com/.default").token
                    logger.info("✅ Got token from Managed Identity for WebSocket authentication")
                    
                    # Return connection details with token
                    # The browser will use this token in the Authorization header when connecting via WebSocket
                    return TokenResponse(
                        token=token,
                        endpoint=ws_url,
                        expires_at=None,  # Token expiration handled by Azure
                    )
                except Exception as e:
                    logger.warning(f"Managed Identity failed: {e}")
                    logger.info("Falling back to API key authentication")
                    # Fall through to API key check below
                    credential = None  # Mark as failed so we check API key
            # Check if we should use API key (either from credential or fallback)
            if isinstance(credential, AzureKeyCredential):
                # Use API key from credential
                api_key = credential.key
                logger.info("✅ Using API key for WebSocket authentication")
            elif credential is None or isinstance(credential, DefaultAzureCredential):
                # Managed Identity failed or not available - try API key from environment
                api_key = os.getenv("AZURE_VOICELIVE_KEY", "")
                if not api_key:
                    raise HTTPException(
                        status_code=503,
                        detail="AZURE_VOICELIVE_KEY not configured and Managed Identity unavailable. Set AZURE_VOICELIVE_KEY for local development."
                    )
                logger.info("✅ Using API key from environment for WebSocket authentication")
            else:
                # Unknown credential type
                logger.error(f"Unknown credential type: {type(credential)}")
                raise HTTPException(
                    status_code=503,
                    detail="Unsupported credential type for project-based endpoints"
                )
            
            # Return API key as "token" - browser will use it in api-key header
            return TokenResponse(
                token=api_key,  # Browser will use this as api-key header
                endpoint=ws_url,
                expires_at=None,
            )
        else:
            # Use REST endpoint for direct endpoints or non-project unified endpoints
            api_key = os.getenv("AZURE_VOICELIVE_KEY", "")
            if not api_key:
                raise HTTPException(status_code=503, detail="AZURE_VOICELIVE_KEY not configured")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Content-Type": "application/json",
                    "api-key": api_key,
                }
                
                response = await client.post(
                    token_url,
                    headers=headers,
                    params={"api-version": api_version},
                    json=session_config,
                )
            
            if response.status_code != 200:
                # Log full error response for debugging
                error_body = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_body)
                    logger.error(
                        f"Token request failed: {response.status_code}\n"
                        f"URL: {token_url}\n"
                        f"Error: {error_detail}\n"
                        f"Full response: {error_body}"
                    )
                    # Include Azure's error message in response (sanitized)
                    raise HTTPException(
                        status_code=502,
                        detail=f"Failed to get ephemeral token: {error_detail}"
                    )
                except (ValueError, KeyError):
                    # If response isn't JSON, use the text
                    logger.error(
                        f"Token request failed: {response.status_code}\n"
                        f"URL: {token_url}\n"
                        f"Response: {error_body}"
                    )
                    raise HTTPException(
                        status_code=502,
                        detail=f"Failed to get ephemeral token: {response.status_code} - {error_body[:200]}"
                    )
            
            data = response.json()
            ephemeral_token = data.get("value", "")
            
            if not ephemeral_token:
                logger.error(f"No token in response: {data}")
                raise HTTPException(status_code=502, detail="No ephemeral token in response")
            
            # Build WebSocket endpoint URL
            if endpoint_type == "direct":
                ws_endpoint = endpoint.replace("https://", "wss://").replace("http://", "ws://")
                ws_url = f"{ws_endpoint}/openai/realtime?api-version={api_version}&deployment={voicelive_service.model}"
            else:
                # Unified endpoint (non-project)
                ws_endpoint = endpoint.replace("https://", "wss://").replace("http://", "ws://")
                ws_url = f"{ws_endpoint}/voice-live/realtime?api-version={api_version}&model={voicelive_service.model}"
            
            return TokenResponse(
                token=ephemeral_token,
                endpoint=ws_url,
                expires_at=data.get("expires_at"),
            )
            
    except httpx.TimeoutException:
        logger.error("Token request timed out")
        raise HTTPException(status_code=504, detail="Token request timed out")
    except httpx.RequestError as e:
        logger.error(f"Token request error: {e}")
        raise HTTPException(status_code=502, detail=f"Token request failed: {str(e)}")


# -----------------------------------------------------------------------------
# VoiceLive v2: Conversation Turn Persistence (for client-side handling)
# -----------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    """A completed turn in the conversation to be persisted"""
    session_id: str
    agent_id: str
    role: str  # 'user' or 'assistant'
    content: str


@router.post("/conversation/turn")
async def persist_conversation_turn(turn: ConversationTurn, user: SecurityContext = Depends(get_current_user)):
    """
    Persist a completed conversation turn to Zep memory.
    
    Used by the frontend in VoiceLive v2 (Direct) mode, where the browser
    handles the audio connection and reports the final transcripts back here.
    
    CRITICAL: Uses authenticated user from SecurityContext to ensure proper
    user attribution and project/department boundaries.
    """
    try:
        # Use authenticated user from SecurityContext
        # This ensures consistent user identity across all systems
        security = SecurityContext(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            roles=user.roles,
            scopes=user.scopes,
            session_id=turn.session_id,
            email=user.email,
            display_name=user.display_name,
        )
            
        # Create context
        voice_context = EnterpriseContext(security=security, context_version="1.0.0")
        voice_context.episodic.conversation_id = turn.session_id
        
        # Ensure session exists with full user metadata
        # This ensures consistent user identity and project/department boundaries
        session_metadata = {
            "tenant_id": security.tenant_id,
            "channel": "voice-direct",
            "agent_id": turn.agent_id,
        }
        # Include user identity metadata for proper attribution
        if security.email:
            session_metadata["email"] = security.email
        if security.display_name:
            session_metadata["display_name"] = security.display_name
        
        await memory_client.get_or_create_session(
            session_id=turn.session_id,
            user_id=security.user_id,
            metadata=session_metadata,
        )
        
        # Add turn
        map_role = MessageRole.USER if turn.role == "user" else MessageRole.ASSISTANT
        voice_context.episodic.add_turn(
            Turn(
                role=map_role,
                content=turn.content,
                agent_id=turn.agent_id if map_role == MessageRole.ASSISTANT else None,
                tool_calls=None,
                token_count=None,
            )
        )
        
        # Persist
        await persist_conversation(voice_context)
        
        return {"status": "success", "message": "Turn persisted"}
        
    except Exception as e:
        logger.error(f"Failed to persist conversation turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))