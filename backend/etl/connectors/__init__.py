"""
Engram ETL Connectors
====================
All data source connectors for the Antigravity Ingestion Router.
"""

# Base classes and registry
from .base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorMetadata,
    ConnectorCategory,
    ConnectorStatus,
    CONNECTOR_REGISTRY,
    register_connector,
    get_connector_class,
    list_available_connectors,
)

# Cloud Storage
from .cloud_storage import S3Connector, AzureBlobConnector, GCSConnector

# Collaboration
from .collaboration import (
    SharePointConnector,
    GoogleDriveConnector,
    OneDriveConnector,
    ConfluenceConnector,
)

# Ticketing
from .ticketing import ServiceNowConnector, JiraConnector, GitHubConnector

# Messaging
from .messaging import SlackConnector, TeamsConnector, EmailConnector

# Data & Integration
from .data import DatabaseConnector, WebhookConnector, LocalConnector

# Legacy connectors (for backwards compatibility)
from .wiki import wiki_connector
from .ticket import ticket_connector
from .git_repo import git_repo_connector

__all__ = [
    # Base
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorMetadata",
    "ConnectorCategory",
    "ConnectorStatus",
    "CONNECTOR_REGISTRY",
    "register_connector",
    "get_connector_class",
    "list_available_connectors",
    # Cloud Storage
    "S3Connector",
    "AzureBlobConnector",
    "GCSConnector",
    # Collaboration
    "SharePointConnector",
    "GoogleDriveConnector",
    "OneDriveConnector",
    "ConfluenceConnector",
    # Ticketing
    "ServiceNowConnector",
    "JiraConnector",
    "GitHubConnector",
    # Messaging
    "SlackConnector",
    "TeamsConnector",
    "EmailConnector",
    # Data & Integration
    "DatabaseConnector",
    "WebhookConnector",
    "LocalConnector",
    # Legacy
    "wiki_connector",
    "ticket_connector",
    "git_repo_connector",
]
