"""
Engram Voice Module

Provides VoiceLive real-time voice interaction with Azure AI Foundry.
"""

from .voicelive_service import VoiceLiveService, voicelive_service

__all__ = [
    "VoiceLiveService",
    "voicelive_service",
]
