"""
Messaging & Communication Connectors
===================================
Slack, Microsoft Teams, Email
"""

import logging
from typing import List, Dict, Any, Optional

from .base import (
    BaseConnector, ConnectorConfig, ConnectorMetadata, 
    ConnectorCategory, ConnectorStatus, register_connector
)

logger = logging.getLogger(__name__)


@register_connector
class SlackConnector(BaseConnector):
    """Slack workspace connector."""
    
    TYPE_ID = "slack"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="slack",
            name="Slack",
            description="Archive channels, threads, and shared files.",
            category=ConnectorCategory.MESSAGING,
            icon="💬",
            default_class="CLASS_B_CHATTER",
            supported_extensions=[".json", ".txt"],  # Messages as JSON
            requires_oauth=True,
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        logger.info("SlackConnector: OAuth Slack App authentication stub")
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"SlackConnector: Listing channel {path or 'all'}")
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Slack fetch requires slack_sdk")


@register_connector
class TeamsConnector(BaseConnector):
    """Microsoft Teams connector."""
    
    TYPE_ID = "teams"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="teams",
            name="Microsoft Teams",
            description="Archive Teams channels and chat history.",
            category=ConnectorCategory.MESSAGING,
            icon="🟦",
            default_class="CLASS_B_CHATTER",
            supported_extensions=[".json", ".txt"],
            requires_oauth=True,
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        logger.info("TeamsConnector: Graph API authentication stub")
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Teams fetch requires Microsoft Graph SDK")


@register_connector
class EmailConnector(BaseConnector):
    """Email (EML/MSG/MBOX) connector."""
    
    TYPE_ID = "email"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="email",
            name="Email",
            description="Ingest EML, MSG, or MBOX exports with thread preservation.",
            category=ConnectorCategory.MESSAGING,
            icon="📧",
            default_class="CLASS_B_CHATTER",
            supported_extensions=[".eml", ".msg", ".mbox"],
            requires_api_key=False,  # File upload, no API
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        # Email connector uses file upload, no auth needed
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        # Not applicable for file upload connector
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Email connector uses direct file upload")
