"""
External integrations for Engram agents.

Provides integrations with:
- GitHub (Projects, Issues)
- Other external services
"""

from .github_client import GitHubClient, get_github_client

__all__ = ["GitHubClient", "get_github_client"]

