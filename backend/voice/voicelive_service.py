"""
VoiceLive Service

Real-time voice interaction using Azure AI VoiceLive SDK.
Provides speech-to-speech conversations with Azure AI Foundry.

Security: NIST AI RMF compliant authentication
- Level 1-2 (POC/Staging): Azure CLI or API Key
- Level 3-5 (Production/Enterprise): Managed Identity via DefaultAzureCredential
"""

import logging
from dataclasses import dataclass
from typing import Optional, Union

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

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
    
    Authentication (NIST AI RMF compliant):
    - DefaultAzureCredential for enterprise (Managed Identity, Service Principal)
    - Falls back to API key for POC/staging if provided
    """
    
    def __init__(self):
        self.settings = get_settings()
        # Use dedicated VoiceLive endpoint (separate from chat gateway)
        self._endpoint = self.settings.azure_voicelive_endpoint
        self._key = self.settings.azure_voicelive_key
        self._model = self.settings.azure_voicelive_model
        self._project_name = self.settings.azure_voicelive_project_name
        self._api_version = self.settings.azure_voicelive_api_version
        
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
        return self._endpoint or "https://zimax.services.ai.azure.com"
    
    @property
    def key(self) -> Optional[str]:
        """Get the VoiceLive API key (for POC/staging)"""
        return self._key
    
    @property
    def model(self) -> str:
        """Get the VoiceLive model"""
        return self._model
    
    @property
    def project_name(self) -> Optional[str]:
        """Get the VoiceLive project name (for unified endpoints)"""
        return self._project_name
    
    @property
    def api_version(self) -> str:
        """Get the VoiceLive API version"""
        return self._api_version
    
    @property
    def is_configured(self) -> bool:
        """Check if VoiceLive is properly configured"""
        # Configured if we have an endpoint (credential can be DefaultAzureCredential)
        return bool(self._endpoint)
    
    def get_credential(self) -> Union[AzureKeyCredential, DefaultAzureCredential]:
        """
        Get the appropriate credential for the environment.
        
        NIST AI RMF Compliance:
        - Enterprise (Level 3-5): Uses DefaultAzureCredential (Managed Identity preferred)
        - POC/Staging (Level 1-2): Falls back to API key if AZURE_VOICELIVE_KEY is set
        
        DefaultAzureCredential tries in order:
        1. Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
        2. Workload Identity (AKS)
        3. Managed Identity (Azure Container Apps, VMs)
        4. Azure CLI (local development)
        5. Azure PowerShell
        6. Interactive browser (if enabled)
        """
        environment = self.settings.environment.lower()
        
        # For production/enterprise, always use DefaultAzureCredential (Managed Identity)
        if environment in ("production", "enterprise", "prod"):
            logger.info("Using DefaultAzureCredential for production (Managed Identity)")
            return DefaultAzureCredential()
        
        # For staging/dev, prefer DefaultAzureCredential but allow API key fallback
        if self._key:
            logger.info("Using API key credential (POC/Staging mode)")
            return AzureKeyCredential(self._key)
        
        # No API key - use DefaultAzureCredential (works with Azure CLI locally)
        logger.info("Using DefaultAzureCredential (Azure CLI or Managed Identity)")
        return DefaultAzureCredential()
    
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
        Uses the configured API version from environment variable.
        """
        if not self._endpoint:
            raise ValueError("AZURE_AI_ENDPOINT not configured")
        
        # Convert HTTP endpoint to WebSocket
        base = self._endpoint.replace("https://", "wss://").replace("http://", "ws://")
        
        # VoiceLive uses the OpenAI realtime path with configurable API version
        api_version = self._api_version
        return f"{base}/openai/realtime?api-version={api_version}&deployment={self._model}"


# Singleton instance
voicelive_service = VoiceLiveService()
