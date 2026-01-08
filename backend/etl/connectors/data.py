"""
Data & Integration Connectors
============================
Database, Webhook, Local Files
"""

import logging
from typing import List, Dict, Any, Optional

from .base import (
    BaseConnector, ConnectorConfig, ConnectorMetadata, 
    ConnectorCategory, ConnectorStatus, register_connector
)

logger = logging.getLogger(__name__)


@register_connector
class DatabaseConnector(BaseConnector):
    """SQL/NoSQL database connector."""
    
    TYPE_ID = "database"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="database",
            name="Database",
            description="Query SQL (Postgres, MySQL) or NoSQL (MongoDB) databases.",
            category=ConnectorCategory.DATABASE,
            icon="🗄️",
            default_class="CLASS_C_OPS",
            supported_extensions=[".json", ".csv"],
            requires_api_key=True,  # Connection string
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        logger.info("DatabaseConnector: Connection string authentication stub")
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"DatabaseConnector: Listing tables/collections in {path or 'default'}")
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Database fetch requires sqlalchemy/pymongo")


@register_connector
class WebhookConnector(BaseConnector):
    """Webhook receiver for real-time data push."""
    
    TYPE_ID = "webhook"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="webhook",
            name="Webhook",
            description="Receive real-time data pushes via HTTP POST.",
            category=ConnectorCategory.DATABASE,
            icon="🔗",
            default_class="CLASS_C_OPS",
            supported_extensions=[".json"],
            requires_api_key=True,  # Webhook secret
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        # Webhook uses signature verification
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        # Not applicable for push-based connector
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Webhook connector receives data, doesn't fetch")


@register_connector
class LocalConnector(BaseConnector):
    """Local file/folder upload connector."""
    
    TYPE_ID = "local"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="local",
            name="Local Upload",
            description="Upload files directly from your computer.",
            category=ConnectorCategory.LOCAL,
            icon="📤",
            default_class="CLASS_B_CHATTER",
            supported_extensions=[
                ".pdf", ".docx", ".xlsx", ".pptx", ".txt",
                ".html", ".csv", ".json", ".eml", ".msg"
            ],
            requires_api_key=False,
            status=ConnectorStatus.HEALTHY,  # Always available
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        # Local upload doesn't need auth
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        # Not applicable for upload connector
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Local connector uses direct file upload")
