"""
Engram Voice Module

Azure Speech and Avatar integration for voice interaction.

Components:
- SpeechService: Speech-to-text and text-to-speech
- AvatarService: Real-time avatar rendering with lip-sync
"""

from .avatar_service import (
    AVATAR_CONFIG,
    AvatarConfig,
    AvatarSession,
    AvatarSpeakRequest,
    AvatarSpeakResult,
    AvatarStyle,
    AzureAvatarService,
    avatar_service,
    avatar_speak,
    close_avatar_session,
    create_avatar_session,
    get_avatar_session,
    interpolate_visemes,
    viseme_to_blendshapes,
)
from .speech_service import (
    VOICE_CONFIG,
    AzureSpeechService,
    SpeechRecognitionResult,
    SpeechSynthesisResult,
    VisemeEvent,
    VoiceId,
    get_voice_for_agent,
    recognize_speech,
    speech_service,
    synthesize_speech,
)
from .voicelive_service import (
    VoiceLiveService,
    VoiceLiveSession,
    voicelive_service,
)

__all__ = [
    # Speech Service
    "AzureSpeechService",
    "speech_service",
    "SpeechRecognitionResult",
    "SpeechSynthesisResult",
    "VisemeEvent",
    "VoiceId",
    "VOICE_CONFIG",
    "recognize_speech",
    "synthesize_speech",
    "get_voice_for_agent",
    # VoiceLive Service
    "VoiceLiveService",
    "VoiceLiveSession",
    "voicelive_service",
    # Avatar Service
    "AzureAvatarService",
    "avatar_service",
    "AvatarConfig",
    "AvatarSession",
    "AvatarSpeakRequest",
    "AvatarSpeakResult",
    "AvatarStyle",
    "AVATAR_CONFIG",
    "create_avatar_session",
    "get_avatar_session",
    "close_avatar_session",
    "avatar_speak",
    "viseme_to_blendshapes",
    "interpolate_visemes",
]
