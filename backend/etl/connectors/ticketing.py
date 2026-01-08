"""
Ticketing & Project Management Connectors
=========================================
ServiceNow, Jira, GitHub Issues
"""

import logging
from typing import List, Dict, Any, Optional

from .base import (
    BaseConnector, ConnectorConfig, ConnectorMetadata, 
    ConnectorCategory, ConnectorStatus, register_connector
)

logger = logging.getLogger(__name__)


@register_connector
class ServiceNowConnector(BaseConnector):
    """ServiceNow ITSM connector."""
    
    TYPE_ID = "servicenow"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="servicenow",
            name="ServiceNow",
            description="Sync incidents, changes, and knowledge articles.",
            category=ConnectorCategory.TICKETING,
            icon="🎫",
            default_class="CLASS_C_OPS",
            supported_extensions=[".json"],  # API returns JSON
            requires_api_key=True,
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        logger.info("ServiceNowConnector: OAuth/Basic authentication stub")
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"ServiceNowConnector: Querying table {path or 'incident'}")
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("ServiceNow fetch requires instance configuration")


@register_connector
class JiraConnector(BaseConnector):
    """Atlassian Jira connector."""
    
    TYPE_ID = "jira"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="jira",
            name="Jira",
            description="Sync issues, epics, and project documentation.",
            category=ConnectorCategory.TICKETING,
            icon="🔷",
            default_class="CLASS_C_OPS",
            supported_extensions=[".json"],
            requires_api_key=True,
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        logger.info("JiraConnector: API token authentication stub")
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"JiraConnector: Querying project {path or 'all'}")
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("Jira fetch requires atlassian-python-api")


@register_connector
class GitHubConnector(BaseConnector):
    """GitHub Issues/PRs connector."""
    
    TYPE_ID = "github"
    
    @property
    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            id="github",
            name="GitHub",
            description="Sync issues, pull requests, and discussions.",
            category=ConnectorCategory.TICKETING,
            icon="🐙",
            default_class="CLASS_C_OPS",
            supported_extensions=[".json", ".md"],
            requires_api_key=True,
            status=self._status,
            docs=self._docs_synced,
        )
    
    async def authenticate(self) -> bool:
        logger.info("GitHubConnector: Token/OAuth authentication stub")
        return True
    
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"GitHubConnector: Listing repo {path or 'all'}")
        return []
    
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        raise NotImplementedError("GitHub fetch requires PyGithub or httpx")
