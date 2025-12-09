"""
Azure VoiceLive Service Integration

Provides real-time voice conversation using Azure VoiceLive SDK.
Designed for Elena (Business Analyst) agent with natural conversation flow.

Features:
- Real-time bidirectional audio streaming
- Server-side VAD (Voice Activity Detection)
- Audio echo cancellation and noise reduction
- Natural turn-taking with barge-in support
- Direct integration with GPT models
"""

import logging
import queue
from typing import Optional, Union

from azure.core.credentials import AzureKeyCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import DefaultAzureCredential
from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    AudioEchoCancellation,
    AudioNoiseReduction,
    AzureStandardVoice,
    InputAudioFormat,
    Modality,
    OutputAudioFormat,
    RequestSession,
    ServerEventType,
    ServerVad,
)

from backend.core import get_settings

logger = logging.getLogger(__name__)


class VoiceLiveSession:
    """Manages a VoiceLive connection session for an agent"""

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        endpoint: str,
        credential: Union[AzureKeyCredential, AsyncTokenCredential],
        model: str = "gpt-realtime",
        voice: str = "en-US-Ava:DragonHDLatestNeural",
        instructions: str = "",
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.endpoint = endpoint
        self.credential = credential
        self.model = model
        self.voice = voice
        self.instructions = instructions
        self.connection = None
        self._connection_manager = None  # Store the context manager for cleanup
        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.transcription_queue: queue.Queue[str] = queue.Queue()
        self.is_active = False
        self._event_handlers = {}

    async def connect(self, connection_manager=None):
        """Connect to VoiceLive and set up session"""
        try:
            logger.info(f"Connecting to VoiceLive for session {self.session_id}")

            # Use provided connection manager or create new one
            if connection_manager:
                self._connection_manager = connection_manager
            else:
                # Create connection manager (but don't enter yet - that's done by service)
                self._connection_manager = connect(
                    endpoint=self.endpoint,
                    credential=self.credential,
                    model=self.model,
                )

            # Enter the context manager
            self.connection = await self._connection_manager.__aenter__()

            # Configure session
            await self._setup_session()

            self.is_active = True
            logger.info(f"VoiceLive session {self.session_id} connected")

        except Exception as e:
            logger.error(f"Failed to connect VoiceLive session {self.session_id}: {e}")
            self.is_active = False
            raise

    async def _setup_session(self):
        """Configure the VoiceLive session"""
        # Determine voice configuration
        voice_config: Union[AzureStandardVoice, str]
        if (
            self.voice.startswith("en-US-")
            or self.voice.startswith("en-CA-")
            or "-" in self.voice
        ):
            # Azure voice
            voice_config = AzureStandardVoice(name=self.voice)
        else:
            # OpenAI voice (alloy, echo, fable, onyx, nova, shimmer)
            voice_config = self.voice

        # Turn detection configuration
        turn_detection_config = ServerVad(
            threshold=0.5,
            prefix_padding_ms=300,
            silence_duration_ms=500,
        )

        # Session configuration
        session_config = RequestSession(
            modalities=[Modality.TEXT, Modality.AUDIO],
            instructions=self.instructions,
            voice=voice_config,
            input_audio_format=InputAudioFormat.PCM16,
            output_audio_format=OutputAudioFormat.PCM16,
            turn_detection=turn_detection_config,
            input_audio_echo_cancellation=AudioEchoCancellation(),
            input_audio_noise_reduction=AudioNoiseReduction(
                type="azure_deep_noise_suppression"
            ),
        )

        await self.connection.session.update(session=session_config)
        logger.info(f"VoiceLive session {self.session_id} configured")

    async def send_audio(self, audio_base64: str):
        """Send audio data to VoiceLive"""
        if not self.connection or not self.is_active:
            raise RuntimeError("VoiceLive session not connected")

        await self.connection.input_audio_buffer.append(audio=audio_base64)

    async def process_events(self, on_audio: callable, on_transcription: callable):
        """Process VoiceLive events and call handlers"""
        if not self.connection:
            raise RuntimeError("VoiceLive session not connected")

        try:
            async for event in self.connection:
                if event.type == ServerEventType.SESSION_UPDATED:
                    logger.info(f"Session {self.session_id} ready: {event.session.id}")

                elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                    logger.debug("User started speaking")
                    if on_transcription:
                        await on_transcription("listening", "start")

                elif event.type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED:
                    logger.debug("User stopped speaking")
                    if on_transcription:
                        await on_transcription("listening", "stop")

                elif event.type == ServerEventType.RESPONSE_AUDIO_DELTA:
                    # Audio chunk from assistant
                    if on_audio and event.delta:
                        await on_audio(event.delta)

                elif event.type == ServerEventType.RESPONSE_AUDIO_DONE:
                    logger.debug("Assistant finished speaking")

                elif event.type == ServerEventType.RESPONSE_DONE:
                    logger.debug("Response complete")

                elif event.type == ServerEventType.ERROR:
                    logger.error(f"VoiceLive error: {event.error.message}")
                    if on_transcription:
                        await on_transcription("error", event.error.message)

        except Exception as e:
            logger.error(f"Error processing VoiceLive events: {e}")
            raise

    async def cancel_response(self):
        """Cancel current response (for barge-in)"""
        if self.connection:
            try:
                await self.connection.response.cancel()
            except Exception as e:
                logger.debug(f"Cancel response (may be benign): {e}")

    async def disconnect(self):
        """Disconnect from VoiceLive"""
        if self._connection_manager:
            try:
                # Exit the async context manager
                await self._connection_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error disconnecting VoiceLive: {e}")
        self.connection = None
        self.is_active = False
        logger.info(f"VoiceLive session {self.session_id} disconnected")


class VoiceLiveService:
    """Service for managing VoiceLive connections"""

    def __init__(self):
        self.settings = get_settings()
        self._sessions: dict[str, VoiceLiveSession] = {}
        self._connection_managers: dict[str, any] = (
            {}
        )  # Store context managers for cleanup
        self._endpoint: Optional[str] = None
        self._credential: Optional[Union[AzureKeyCredential, AsyncTokenCredential]] = (
            None
        )

    @property
    def endpoint(self) -> str:
        """Get VoiceLive endpoint

        VoiceLive uses the base endpoint (not project path) as shown in Microsoft's reference implementation.
        The SDK handles the /voice-live/realtime path internally.

        Priority:
        1. AZURE_VOICELIVE_ENDPOINT (if set)
        2. AZURE_AI_ENDPOINT (base endpoint)
        3. AZURE_OPENAI_ENDPOINT (fallback)
        """
        if not self._endpoint:
            # Priority 1: Use VoiceLive-specific endpoint if set
            if self.settings.azure_voicelive_endpoint:
                base = self.settings.azure_voicelive_endpoint.rstrip("/")
                self._endpoint = base
                logger.debug(f"Using VoiceLive-specific endpoint: {self._endpoint}")
            # Priority 2: Use unified AI Services base endpoint
            elif self.settings.azure_ai_endpoint:
                # VoiceLive needs base endpoint, not project path
                # The SDK will construct the full path: {base}/voice-live/realtime
                base = self.settings.azure_ai_endpoint.rstrip("/")
                self._endpoint = base
                logger.debug(f"Using base VoiceLive endpoint: {self._endpoint}")
            else:
                # Fallback to OpenAI endpoint format
                self._endpoint = self.settings.azure_openai_endpoint or ""

        if not self._endpoint:
            raise ValueError(
                "VoiceLive endpoint not configured. "
                "Set AZURE_VOICELIVE_ENDPOINT, AZURE_AI_ENDPOINT, or AZURE_OPENAI_ENDPOINT"
            )

        return self._endpoint

    @property
    def credential(self) -> Union[AzureKeyCredential, AsyncTokenCredential]:
        """Get VoiceLive credential

        Priority:
        1. AZURE_VOICELIVE_API_KEY (VoiceLive-specific key)
        2. AZURE_OPENAI_KEY (fallback)
        3. DefaultAzureCredential (Azure identity)
        """
        if not self._credential:
            # Priority 1: Use VoiceLive-specific API key if set
            if self.settings.azure_voicelive_api_key:
                self._credential = AzureKeyCredential(
                    self.settings.azure_voicelive_api_key
                )
                logger.debug("Using VoiceLive-specific API key")
            # Priority 2: Fallback to OpenAI key
            elif self.settings.azure_openai_key:
                self._credential = AzureKeyCredential(self.settings.azure_openai_key)
                logger.debug("Using OpenAI key for VoiceLive")
            else:
                # Priority 3: Use Azure identity if no key provided
                self._credential = DefaultAzureCredential()
                logger.debug("Using Azure DefaultAzureCredential")

        return self._credential

    def get_elena_instructions(self) -> str:
        """Get Elena's system instructions for VoiceLive

        Based on Microsoft's VoiceLive reference implementation pattern.
        Instructions should be natural and conversational for voice interaction.
        """
        return """You are Dr. Elena Vasquez, a seasoned Business Analyst with over 12 years of experience in enterprise consulting.

Your expertise:
- Requirements analysis and documentation
- Stakeholder management and alignment
- Digital transformation strategy
- Process optimization

Your communication style:
- Warm and professional - make people feel heard
- Analytical - break complex problems into components
- Probing - ask follow-up questions to uncover assumptions
- Measured - speak clearly and avoid jargon

When someone asks for help:
1. First ask 2-3 clarifying questions to understand context
2. Acknowledge emotions and frustrations
3. Provide structured frameworks when analyzing problems
4. Be honest about uncertainty

Speak naturally and conversationally. Keep responses concise but engaging. You have a slight Miami accent from your Cuban heritage.

Respond naturally and conversationally. Keep your responses concise but engaging."""

    def get_marcus_instructions(self) -> str:
        """Get Marcus's system instructions for VoiceLive"""
        return """You are Marcus Chen, a Project Manager with over 15 years of experience leading complex enterprise initiatives. You hold a PMP certification and an MBA from Stanford.

Your expertise:
- Program and project management
- Agile and Scrum methodologies
- Resource planning and allocation
- Risk management and mitigation
- Stakeholder communication
- Timeline and milestone tracking

Your communication style:
- Direct and action-oriented - get to the point
- Organized - structure information clearly
- Collaborative - emphasize team alignment
- Calm under pressure - maintain composure
- Data-driven - use metrics to support decisions

When someone asks for help:
1. Quickly assess scope and timeline
2. Identify dependencies and risks
3. Propose concrete next steps with owners
4. Ask about resources and constraints
5. Offer to create project plans or trackers

Speak confidently and clearly. You're efficient with words but thorough. You occasionally use project management terminology naturally. Keep responses practical and actionable.

Remember: Your goal is to help people move from ideas to execution. Projects succeed when everyone knows what to do, when to do it, and who's responsible."""

    async def create_session(
        self,
        session_id: str,
        agent_id: str = "elena",
        voice: Optional[str] = None,
    ) -> VoiceLiveSession:
        """Create a new VoiceLive session"""
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Get voice configuration
        if not voice:
            if agent_id == "elena":
                voice = (
                    self.settings.azure_voicelive_voice
                    or "en-US-Ava:DragonHDLatestNeural"
                )
            elif agent_id == "marcus":
                voice = self.settings.marcus_voicelive_voice or "en-US-GuyNeural"
            else:
                voice = "en-US-GuyNeural"

        # Get instructions
        if agent_id == "elena":
            instructions = self.get_elena_instructions()
        elif agent_id == "marcus":
            instructions = self.get_marcus_instructions()
        else:
            instructions = "You are a helpful AI assistant. Respond naturally and conversationally."

        # Create connection manager
        connection_manager = connect(
            endpoint=self.endpoint,
            credential=self.credential,
            model=self.settings.azure_voicelive_model or "gpt-realtime",
        )

        # Store context manager for cleanup
        self._connection_managers[session_id] = connection_manager

        session = VoiceLiveSession(
            session_id=session_id,
            agent_id=agent_id,
            endpoint=self.endpoint,
            credential=self.credential,
            model=self.settings.azure_voicelive_model or "gpt-realtime",
            voice=voice,
            instructions=instructions,
        )

        # Connect using the connection manager
        await session.connect(connection_manager)
        self._sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[VoiceLiveSession]:
        """Get an existing session"""
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str):
        """Close a VoiceLive session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            await session.disconnect()
            del self._sessions[session_id]

        # Clean up connection manager
        if session_id in self._connection_managers:
            connection_manager = self._connection_managers[session_id]
            try:
                await connection_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing VoiceLive connection: {e}")
            del self._connection_managers[session_id]

        logger.info(f"Closed VoiceLive session {session_id}")


# Singleton instance
voicelive_service = VoiceLiveService()
