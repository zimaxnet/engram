"""
Azure AI Avatar Service Integration

Provides:
- Real-time avatar rendering with lip-sync
- Avatar session management
- Viseme-to-blendshape mapping
- WebRTC streaming support

Uses Azure AI Avatar (formerly Azure Communication Services Avatar).
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from backend.core import get_settings

logger = logging.getLogger(__name__)


class AvatarStyle(str, Enum):
    """Available avatar styles"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"


@dataclass
class AvatarConfig:
    """Configuration for an avatar"""
    avatar_id: str
    voice_name: str
    style: AvatarStyle
    background_color: str
    character_style: str  # e.g., "business", "casual"


# Avatar configurations for each agent
AVATAR_CONFIG = {
    "elena": AvatarConfig(
        avatar_id="lisa",  # Azure's professional female avatar
        voice_name="en-US-JennyNeural",
        style=AvatarStyle.PROFESSIONAL,
        background_color="#0a0e1a",
        character_style="business"
    ),
    "marcus": AvatarConfig(
        avatar_id="max",  # Azure's professional male avatar
        voice_name="en-US-GuyNeural",
        style=AvatarStyle.PROFESSIONAL,
        background_color="#0a0e1a",
        character_style="business"
    ),
}


@dataclass
class AvatarSession:
    """Active avatar session"""
    session_id: str
    agent_id: str
    config: AvatarConfig
    ice_servers: list[dict]
    offer_sdp: Optional[str] = None
    answer_sdp: Optional[str] = None
    is_active: bool = True


@dataclass
class AvatarSpeakRequest:
    """Request to make avatar speak"""
    text: str
    ssml: Optional[str] = None
    visemes: Optional[list[dict]] = None


@dataclass
class AvatarSpeakResult:
    """Result from avatar speak"""
    success: bool
    duration_ms: int
    audio_url: Optional[str] = None
    error: Optional[str] = None


class AzureAvatarService:
    """
    Azure AI Avatar Service client.
    
    Manages avatar sessions and real-time rendering.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._sessions: dict[str, AvatarSession] = {}
        self._initialized = False
    
    async def create_session(
        self,
        session_id: str,
        agent_id: str = "elena"
    ) -> AvatarSession:
        """
        Create a new avatar session.
        
        Args:
            session_id: Unique session identifier
            agent_id: Which agent avatar to use
            
        Returns:
            AvatarSession with connection details
        """
        config = AVATAR_CONFIG.get(agent_id, AVATAR_CONFIG["elena"])
        
        # In production, this would create a session with Azure
        # For now, return a mock session
        session = AvatarSession(
            session_id=session_id,
            agent_id=agent_id,
            config=config,
            ice_servers=[
                {
                    "urls": ["stun:stun.l.google.com:19302"],
                }
            ],
            is_active=True
        )
        
        self._sessions[session_id] = session
        logger.info(f"Created avatar session: {session_id} for agent {agent_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[AvatarSession]:
        """Get an existing avatar session"""
        return self._sessions.get(session_id)
    
    async def close_session(self, session_id: str) -> bool:
        """Close an avatar session"""
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False
            del self._sessions[session_id]
            logger.info(f"Closed avatar session: {session_id}")
            return True
        return False
    
    async def speak(
        self,
        session_id: str,
        text: str,
        visemes: Optional[list[dict]] = None
    ) -> AvatarSpeakResult:
        """
        Make the avatar speak with lip-sync.
        
        Args:
            session_id: Session to use
            text: Text to speak
            visemes: Pre-computed viseme data for lip-sync
            
        Returns:
            AvatarSpeakResult
        """
        session = await self.get_session(session_id)
        if not session:
            return AvatarSpeakResult(
                success=False,
                duration_ms=0,
                error="Session not found"
            )
        
        if not session.is_active:
            return AvatarSpeakResult(
                success=False,
                duration_ms=0,
                error="Session is not active"
            )
        
        try:
            # In production, this would:
            # 1. Send text/SSML to Azure Avatar API
            # 2. Stream audio to WebRTC connection
            # 3. Apply viseme animations in real-time
            
            # Estimate duration (rough: ~100ms per word)
            word_count = len(text.split())
            duration_ms = word_count * 150
            
            logger.info(f"Avatar speaking: {text[:50]}... (session: {session_id})")
            
            return AvatarSpeakResult(
                success=True,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Avatar speak error: {e}")
            return AvatarSpeakResult(
                success=False,
                duration_ms=0,
                error=str(e)
            )
    
    async def set_expression(
        self,
        session_id: str,
        expression: str
    ) -> bool:
        """
        Set the avatar's facial expression.
        
        Args:
            session_id: Session to use
            expression: Expression name (e.g., "smile", "neutral", "thinking")
            
        Returns:
            Success status
        """
        session = await self.get_session(session_id)
        if not session or not session.is_active:
            return False
        
        # In production, this would send expression command to avatar
        logger.info(f"Avatar expression: {expression} (session: {session_id})")
        return True
    
    async def set_gesture(
        self,
        session_id: str,
        gesture: str
    ) -> bool:
        """
        Trigger an avatar gesture/animation.
        
        Args:
            session_id: Session to use
            gesture: Gesture name (e.g., "nod", "wave", "thinking")
            
        Returns:
            Success status
        """
        session = await self.get_session(session_id)
        if not session or not session.is_active:
            return False
        
        # In production, this would trigger gesture animation
        logger.info(f"Avatar gesture: {gesture} (session: {session_id})")
        return True
    
    def get_webrtc_config(self, session: AvatarSession) -> dict:
        """
        Get WebRTC configuration for client connection.
        
        Returns configuration needed for browser WebRTC setup.
        """
        return {
            "iceServers": session.ice_servers,
            "avatarId": session.config.avatar_id,
            "backgroundColor": session.config.background_color,
            "characterStyle": session.config.character_style,
        }


# Viseme to blendshape mapping for custom avatar implementations
VISEME_BLENDSHAPE_MAP = {
    0: {"name": "sil", "shapes": {"jawOpen": 0.0}},  # Silence
    1: {"name": "aa", "shapes": {"jawOpen": 0.6, "mouthFunnel": 0.2}},
    2: {"name": "aa", "shapes": {"jawOpen": 0.5, "mouthFunnel": 0.3}},
    3: {"name": "ao", "shapes": {"jawOpen": 0.4, "mouthPucker": 0.3}},
    4: {"name": "ey", "shapes": {"jawOpen": 0.3, "mouthSmile": 0.4}},
    5: {"name": "er", "shapes": {"jawOpen": 0.3, "mouthFunnel": 0.4}},
    6: {"name": "ih", "shapes": {"jawOpen": 0.2, "mouthSmile": 0.3}},
    7: {"name": "uw", "shapes": {"jawOpen": 0.2, "mouthPucker": 0.6}},
    8: {"name": "ow", "shapes": {"jawOpen": 0.4, "mouthPucker": 0.4}},
    9: {"name": "aw", "shapes": {"jawOpen": 0.5, "mouthFunnel": 0.2}},
    10: {"name": "oy", "shapes": {"jawOpen": 0.3, "mouthPucker": 0.3}},
    11: {"name": "ay", "shapes": {"jawOpen": 0.4, "mouthSmile": 0.2}},
    12: {"name": "h", "shapes": {"jawOpen": 0.3}},
    13: {"name": "r", "shapes": {"jawOpen": 0.2, "mouthFunnel": 0.3}},
    14: {"name": "l", "shapes": {"jawOpen": 0.2, "tongueOut": 0.1}},
    15: {"name": "s", "shapes": {"jawOpen": 0.1, "mouthSmile": 0.2}},
    16: {"name": "sh", "shapes": {"jawOpen": 0.1, "mouthPucker": 0.3}},
    17: {"name": "th", "shapes": {"jawOpen": 0.1, "tongueOut": 0.2}},
    18: {"name": "f", "shapes": {"jawOpen": 0.1, "mouthFunnel": 0.1}},
    19: {"name": "d", "shapes": {"jawOpen": 0.2}},
    20: {"name": "k", "shapes": {"jawOpen": 0.15}},
    21: {"name": "p", "shapes": {"jawOpen": 0.0, "mouthPress": 0.5}},
}


def viseme_to_blendshapes(viseme_id: int) -> dict:
    """
    Convert a viseme ID to blendshape values.
    
    Used for custom avatar implementations that use blendshapes
    instead of Azure's built-in viseme support.
    
    Args:
        viseme_id: Viseme ID (0-21)
        
    Returns:
        Dictionary of blendshape names to values (0.0-1.0)
    """
    mapping = VISEME_BLENDSHAPE_MAP.get(viseme_id, VISEME_BLENDSHAPE_MAP[0])
    return mapping["shapes"]


def interpolate_visemes(
    visemes: list[dict],
    current_time_ms: int,
    smoothing: float = 0.3
) -> dict:
    """
    Interpolate between visemes for smooth animation.
    
    Args:
        visemes: List of viseme events with time_ms and viseme_id
        current_time_ms: Current playback time
        smoothing: Smoothing factor (0-1)
        
    Returns:
        Interpolated blendshape values
    """
    if not visemes:
        return viseme_to_blendshapes(0)
    
    # Find surrounding visemes
    prev_viseme = visemes[0]
    next_viseme = visemes[0]
    
    for i, v in enumerate(visemes):
        if v["time_ms"] <= current_time_ms:
            prev_viseme = v
            if i + 1 < len(visemes):
                next_viseme = visemes[i + 1]
            else:
                next_viseme = v
        else:
            break
    
    # Calculate interpolation factor
    if prev_viseme["time_ms"] == next_viseme["time_ms"]:
        t = 0.0
    else:
        t = (current_time_ms - prev_viseme["time_ms"]) / (
            next_viseme["time_ms"] - prev_viseme["time_ms"]
        )
    
    # Apply smoothing
    t = t ** (1 / (1 + smoothing))
    
    # Interpolate blendshapes
    prev_shapes = viseme_to_blendshapes(prev_viseme["viseme_id"])
    next_shapes = viseme_to_blendshapes(next_viseme["viseme_id"])
    
    result = {}
    all_keys = set(prev_shapes.keys()) | set(next_shapes.keys())
    
    for key in all_keys:
        prev_val = prev_shapes.get(key, 0.0)
        next_val = next_shapes.get(key, 0.0)
        result[key] = prev_val + (next_val - prev_val) * t
    
    return result


# Singleton service
avatar_service = AzureAvatarService()


# Convenience functions
async def create_avatar_session(session_id: str, agent_id: str = "elena") -> AvatarSession:
    """Create a new avatar session"""
    return await avatar_service.create_session(session_id, agent_id)


async def get_avatar_session(session_id: str) -> Optional[AvatarSession]:
    """Get an existing avatar session"""
    return await avatar_service.get_session(session_id)


async def close_avatar_session(session_id: str) -> bool:
    """Close an avatar session"""
    return await avatar_service.close_session(session_id)


async def avatar_speak(
    session_id: str,
    text: str,
    visemes: Optional[list[dict]] = None
) -> AvatarSpeakResult:
    """Make the avatar speak"""
    return await avatar_service.speak(session_id, text, visemes)

