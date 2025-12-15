"""
VoiceLive Service

Real-time voice interaction using Azure AI VoiceLive SDK.
Provides speech-to-speech conversations with Azure AI Foundry.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from backend.core import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AgentVoiceConfig:
    """Voice configuration for an agent"""
    voice_name: str
    instructions: str
    personality: str


class VoiceLiveService:
    """
    VoiceLive Service for real-time voice interactions.
    
    Uses Azure AI VoiceLive SDK for:
    - Real-time bidirectional audio streaming
    - Server-side VAD (Voice Activity Detection)
    - Natural turn-taking with barge-in support
    - Direct integration with GPT models (gpt-realtime v2025-08-28)
    """
    
    def __init__(self):
        self.settings = get_settings()
        # Use dedicated VoiceLive endpoint (separate from chat gateway)
        self._endpoint = self.settings.azure_voicelive_endpoint
        self._key = self.settings.azure_voicelive_key
        self._model = self.settings.azure_voicelive_model
        
        # Voice configurations per agent
        self._agent_voices = {
            "elena": AgentVoiceConfig(
                voice_name=self.settings.azure_voicelive_voice,  # en-US-Ava:DragonHDLatestNeural
                instructions=self._get_elena_instructions(),
                personality="warm, measured, professional with Miami accent"
            ),
            "marcus": AgentVoiceConfig(
                voice_name=self.settings.marcus_voicelive_voice,  # en-US-GuyNeural
                instructions=self._get_marcus_instructions(),
                personality="confident, energetic, Pacific Northwest professional"
            ),
        }
    
    @property
    def endpoint(self) -> str:
        """Get the VoiceLive endpoint"""
        return self._endpoint or ""
    
    @property
    def key(self) -> Optional[str]:
        """Get the VoiceLive API key"""
        return self._key
    
    @property
    def model(self) -> str:
        """Get the VoiceLive model"""
        return self._model
    
    @property
    def is_configured(self) -> bool:
        """Check if VoiceLive is properly configured"""
        return bool(self._endpoint and self._key)
    
    def get_agent_voice_config(self, agent_id: str) -> AgentVoiceConfig:
        """Get voice configuration for an agent"""
        return self._agent_voices.get(agent_id, self._agent_voices["elena"])
    
    def get_elena_instructions(self) -> str:
        """Get Elena's voice assistant instructions"""
        return self._get_elena_instructions()
    
    def get_marcus_instructions(self) -> str:
        """Get Marcus's voice assistant instructions"""
        return self._get_marcus_instructions()
    
    def _get_elena_instructions(self) -> str:
        """Elena's system instructions for VoiceLive"""
        return """You are Elena, an expert Business Analyst and Requirements Engineer at Engram.

Your communication style:
- Warm and approachable, with a professional demeanor
- Speak naturally and conversationally, as if talking to a colleague
- Be concise but thorough - aim for clear, actionable responses
- Use a measured pace, pausing thoughtfully when appropriate

Your expertise:
- Requirements gathering and analysis
- Stakeholder interviews and facilitation
- Process mapping and optimization
- User story creation and refinement
- Business case development

When speaking:
- Listen actively and ask clarifying questions
- Summarize key points to confirm understanding
- Offer structured recommendations when appropriate
- If you need to think, say so naturally ("Let me consider that...")

Remember: You're having a real conversation. Be helpful, be human."""

    def _get_marcus_instructions(self) -> str:
        """Marcus's system instructions for VoiceLive"""
        return """You are Marcus, an experienced Technical Project Manager at Engram.

Your communication style:
- Confident and energetic, with clear direction
- Direct and pragmatic - get to the point efficiently
- Speak with authority but remain approachable
- Bring positive energy while staying focused

Your expertise:
- Project planning and execution
- Risk assessment and mitigation
- Team coordination and resource management
- Timeline and milestone tracking
- Stakeholder communication

When speaking:
- Be decisive and action-oriented
- Break down complex topics into manageable pieces
- Provide concrete next steps when possible
- If there are risks or blockers, address them directly

Remember: You're a leader in the conversation. Guide it productively."""

    def build_websocket_endpoint(self, session_id: str) -> str:
        """
        Build the VoiceLive WebSocket endpoint URL.
        
        The VoiceLive SDK expects a specific endpoint format for real-time audio.
        """
        if not self._endpoint:
            raise ValueError("AZURE_AI_ENDPOINT not configured")
        
        # Convert HTTP endpoint to WebSocket
        base = self._endpoint.replace("https://", "wss://").replace("http://", "ws://")
        
        # VoiceLive uses the OpenAI realtime path
        return f"{base}/openai/realtime?api-version=2024-10-01-preview&deployment={self._model}"


# Singleton instance
voicelive_service = VoiceLiveService()
