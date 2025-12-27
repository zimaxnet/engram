"""
GitHub API Client for Engram Agents

Provides tools for Elena and Marcus to interact with GitHub Projects,
Issues, and track implementation plan progress.
"""

import logging
import os
from typing import Optional, Dict, List, Any
import httpx

from backend.core import get_settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Client for interacting with GitHub API.
    
    Supports:
    - Creating/updating issues
    - Managing GitHub Projects
    - Querying project status
    - Tracking task progress
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.token = os.getenv("GITHUB_TOKEN") or self.settings.github_token
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER") or "zimaxnet"
        self.repo_name = os.getenv("GITHUB_REPO_NAME") or "engram"
        self.base_url = "https://api.github.com"
        self._http_client = None
        
        if not self.token:
            logger.warning("GitHub token not configured. GitHub integration will be limited.")
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy-load the async HTTP client"""
        if self._http_client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0
            )
        return self._http_client
    
    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a GitHub issue.
        
        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of label names
            assignees: List of GitHub usernames to assign
            
        Returns:
            Issue data including issue number and URL
        """
        if not self.token:
            return {
                "success": False,
                "error": "GitHub token not configured",
                "issue_number": None,
                "issue_url": None,
            }
        
        try:
            payload = {
                "title": title,
                "body": body,
            }
            if labels:
                payload["labels"] = labels
            if assignees:
                payload["assignees"] = assignees
            
            response = await self.http_client.post(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Created GitHub issue #{data['number']}: {title}")
            
            return {
                "success": True,
                "issue_number": data["number"],
                "issue_url": data["html_url"],
                "issue_id": data["id"],
            }
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            return {
                "success": False,
                "error": str(e),
                "issue_number": None,
                "issue_url": None,
            }
    
    async def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,  # "open" or "closed"
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update a GitHub issue.
        
        Args:
            issue_number: Issue number
            title: New title (optional)
            body: New body (optional)
            state: New state - "open" or "closed" (optional)
            labels: New labels (optional)
            
        Returns:
            Updated issue data
        """
        if not self.token:
            return {"success": False, "error": "GitHub token not configured"}
        
        try:
            payload = {}
            if title:
                payload["title"] = title
            if body:
                payload["body"] = body
            if state:
                payload["state"] = state
            if labels is not None:
                payload["labels"] = labels
            
            if not payload:
                return {"success": False, "error": "No updates provided"}
            
            response = await self.http_client.patch(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Updated GitHub issue #{issue_number}")
            
            return {
                "success": True,
                "issue_number": data["number"],
                "issue_url": data["html_url"],
                "state": data["state"],
            }
        except Exception as e:
            logger.error(f"Failed to update GitHub issue #{issue_number}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_project_status(self, project_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Get status of GitHub Project.
        
        Args:
            project_number: Project number (optional, will use default if not provided)
            
        Returns:
            Project status including task counts, progress metrics
        """
        if not self.token:
            return {
                "success": False,
                "error": "GitHub token not configured",
                "status": "unknown"
            }
        
        try:
            # For now, return a summary based on issues
            # In the future, we can use GitHub Projects API v2
            response = await self.http_client.get(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues",
                params={
                    "state": "all",
                    "labels": "production-grade-system",
                    "per_page": 100,
                }
            )
            response.raise_for_status()
            issues = response.json()
            
            # Count by state
            open_issues = [i for i in issues if i["state"] == "open"]
            closed_issues = [i for i in issues if i["state"] == "closed"]
            
            # Count by label/priority
            critical_issues = [i for i in open_issues if any("critical" in l.get("name", "").lower() for l in i.get("labels", []))]
            
            total = len(issues)
            completed = len(closed_issues)
            progress_pct = (completed / total * 100) if total > 0 else 0
            
            return {
                "success": True,
                "total_tasks": total,
                "completed_tasks": completed,
                "open_tasks": len(open_issues),
                "critical_tasks": len(critical_issues),
                "progress_percentage": round(progress_pct, 1),
                "status": "on_track" if progress_pct >= 50 else "behind" if progress_pct < 25 else "in_progress",
            }
        except Exception as e:
            logger.error(f"Failed to get project status: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "unknown"
            }
    
    async def list_issues(
        self,
        labels: Optional[List[str]] = None,
        state: str = "open",
        assignee: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List GitHub issues.
        
        Args:
            labels: Filter by labels
            state: "open" or "closed"
            assignee: Filter by assignee username
            
        Returns:
            List of issues
        """
        if not self.token:
            return []
        
        try:
            params = {
                "state": state,
                "per_page": 100,
            }
            if labels:
                params["labels"] = ",".join(labels)
            if assignee:
                params["assignee"] = assignee
            
            response = await self.http_client.get(
                f"/repos/{self.repo_owner}/{self.repo_name}/issues",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list issues: {e}")
            return []
    
    async def add_issue_to_project(
        self,
        issue_number: int,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add an issue to a GitHub Project.
        
        Note: This requires GitHub Projects API v2 which uses GraphQL.
        For now, this is a placeholder for future implementation.
        
        Args:
            issue_number: Issue number to add
            project_id: Project ID (optional)
            
        Returns:
            Success status
        """
        # TODO: Implement using GraphQL API
        # This requires more complex setup with project IDs
        logger.warning("add_issue_to_project not yet implemented - requires GraphQL API")
        return {
            "success": False,
            "error": "Not yet implemented - requires GraphQL API setup",
            "note": "Issues can be manually added to projects via GitHub UI"
        }
    
    async def close(self):
        """Close the HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Singleton instance
_github_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    """Get or create the GitHub client singleton"""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client

