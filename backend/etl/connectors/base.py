"""
Connector Base Classes
=====================
System: Engram Context Ecology Platform
Author: Zimax Networks LC

Abstract base for all data source connectors.
Connectors handle authentication, fetching, and routing to Antigravity.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectorStatus(Enum):
    """Operational status of a connector."""
    HEALTHY = "healthy"
    SYNCING = "syncing"
    PAUSED = "paused"
    ERROR = "error"
    PENDING = "pending"  # Not yet configured


class ConnectorCategory(Enum):
    """Category of connector for UI grouping."""
    CLOUD_STORAGE = "cloud_storage"
    COLLABORATION = "collaboration"
    TICKETING = "ticketing"
    MESSAGING = "messaging"
    DATABASE = "database"
    LOCAL = "local"


@dataclass
class ConnectorConfig:
    """Configuration for a connector instance."""
    name: str
    connector_type: str
    enabled: bool = True
    scope: Optional[str] = None  # Path, bucket, channel, etc.
    credentials: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None  # Cron expression
    tags: List[str] = field(default_factory=list)
    sensitivity_override: Optional[str] = None  # high, moderate, low
    max_file_size_mb: int = 100
    file_types: List[str] = field(default_factory=list)  # Empty = all


@dataclass
class ConnectorMetadata:
    """Metadata describing a connector type."""
    id: str
    name: str
    description: str
    category: ConnectorCategory
    icon: str  # Emoji or icon name
    default_class: str  # CLASS_A_TRUTH, CLASS_B_CHATTER, CLASS_C_OPS
    supported_extensions: List[str]
    requires_oauth: bool = False
    requires_api_key: bool = False
    status: ConnectorStatus = ConnectorStatus.PENDING
    docs: int = 0
    last_sync: Optional[str] = None


class BaseConnector(ABC):
    """
    Abstract base class for all Engram connectors.
    
    Subclasses must implement:
    - metadata: Static info about the connector
    - authenticate: Establish credentials
    - list_items: Enumerate available items
    - fetch_item: Retrieve a single item
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self._status = ConnectorStatus.PENDING
        self._last_error: Optional[str] = None
        self._docs_synced = 0
    
    @property
    @abstractmethod
    def metadata(self) -> ConnectorMetadata:
        """Return static metadata about this connector type."""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the data source.
        Returns True if successful.
        """
        pass
    
    @abstractmethod
    async def list_items(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available items in the data source.
        
        Returns list of dicts with at least:
        - id: Unique identifier
        - name: Display name
        - type: file, folder, etc.
        - modified: Last modified timestamp
        """
        pass
    
    @abstractmethod
    async def fetch_item(self, item_id: str) -> tuple[bytes, str, str]:
        """
        Fetch a single item.
        
        Returns:
        - content: Raw bytes
        - filename: Name for classification
        - content_type: MIME type
        """
        pass
    
    async def sync(self, user_id: str) -> Dict[str, Any]:
        """
        Perform a full sync of the data source.
        
        Fetches all items and routes through Antigravity.
        """
        from backend.etl.antigravity_router import antigravity_router
        
        self._status = ConnectorStatus.SYNCING
        synced = 0
        errors = []
        
        try:
            if not await self.authenticate():
                raise Exception("Authentication failed")
            
            items = await self.list_items(self.config.scope)
            
            for item in items:
                try:
                    content, filename, content_type = await self.fetch_item(item["id"])
                    
                    # Route through Antigravity
                    chunks = antigravity_router.ingest_bytes(
                        content, filename, content_type
                    )
                    
                    synced += 1
                    self._docs_synced += 1
                    
                    logger.info(f"{self.metadata.name}: Synced {filename} ({len(chunks)} chunks)")
                    
                except Exception as e:
                    errors.append({"item": item["name"], "error": str(e)})
                    logger.error(f"{self.metadata.name}: Failed to sync {item['name']}: {e}")
            
            self._status = ConnectorStatus.HEALTHY
            return {
                "success": True,
                "synced": synced,
                "errors": errors,
            }
            
        except Exception as e:
            self._status = ConnectorStatus.ERROR
            self._last_error = str(e)
            return {
                "success": False,
                "synced": synced,
                "errors": [{"error": str(e)}],
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connector status."""
        return {
            "id": self.metadata.id,
            "name": self.config.name,
            "type": self.metadata.name,
            "status": self._status.value,
            "docs": self._docs_synced,
            "last_error": self._last_error,
            "last_sync": self.metadata.last_sync,
        }


# Registry of all available connectors
CONNECTOR_REGISTRY: Dict[str, type] = {}


def register_connector(connector_class: type):
    """Decorator to register a connector class."""
    CONNECTOR_REGISTRY[connector_class.TYPE_ID] = connector_class
    return connector_class


def get_connector_class(type_id: str) -> Optional[type]:
    """Get connector class by type ID."""
    return CONNECTOR_REGISTRY.get(type_id)


def list_available_connectors() -> List[ConnectorMetadata]:
    """List all registered connector types."""
    connectors = []
    for cls in CONNECTOR_REGISTRY.values():
        instance = cls(ConnectorConfig(name="temp", connector_type=cls.TYPE_ID))
        connectors.append(instance.metadata)
    return connectors
