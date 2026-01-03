"""
External integrations for Engram agents.

Provides integrations with:
- Microsoft Graph (Email, OneDrive, Calendar)
- GitHub (Projects, Issues)
- Other external services
"""

from .github_client import GitHubClient, get_github_client
from .graph_client import GraphClient, graph_client

__all__ = [
    "GitHubClient",
    "get_github_client",
    "GraphClient",
    "graph_client",
]
