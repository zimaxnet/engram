"""
GitHub Tools for Engram Agents

Tools that allow Elena and Marcus to interact with GitHub Projects
and track implementation plan progress.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from backend.integrations.github_client import get_github_client

logger = logging.getLogger(__name__)


@tool("create_github_issue")
async def create_github_issue_tool(
    title: str,
    body: str,
    labels: Optional[str] = None,
    assignee: Optional[str] = None,
) -> str:
    """
    Create a GitHub issue for tracking a task.
    
    Use this when you need to create a task in GitHub Projects or track work items.
    
    Args:
        title: Issue title
        body: Issue description (markdown supported)
        labels: Comma-separated list of labels (e.g., "production-grade-system,Layer 6: Guardrails")
        assignee: GitHub username to assign (optional)
        
    Returns:
        Issue number and URL if successful, error message otherwise
    """
    try:
        client = get_github_client()
        
        label_list = [l.strip() for l in labels.split(",")] if labels else None
        assignee_list = [assignee] if assignee else None
        
        result = await client.create_issue(
            title=title,
            body=body,
            labels=label_list,
            assignees=assignee_list,
        )
        
        if result["success"]:
            return f"✅ Created GitHub issue #{result['issue_number']}: {result['issue_url']}"
        else:
            return f"❌ Failed to create issue: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error creating GitHub issue: {e}")
        return f"❌ Error creating issue: {e}"


@tool("update_github_issue")
async def update_github_issue_tool(
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[str] = None,
) -> str:
    """
    Update an existing GitHub issue.
    
    Use this to update task status, add progress notes, or close completed tasks.
    
    Args:
        issue_number: GitHub issue number
        title: New title (optional)
        body: New body/description (optional)
        state: "open" or "closed" (optional)
        labels: Comma-separated list of labels (optional)
        
    Returns:
        Success message or error
    """
    try:
        client = get_github_client()
        
        label_list = [l.strip() for l in labels.split(",")] if labels else None
        
        result = await client.update_issue(
            issue_number=issue_number,
            title=title,
            body=body,
            state=state,
            labels=label_list,
        )
        
        if result["success"]:
            status = f" ({result.get('state', 'updated')})" if state else ""
            return f"✅ Updated issue #{issue_number}{status}: {result.get('issue_url', '')}"
        else:
            return f"❌ Failed to update issue: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error updating GitHub issue: {e}")
        return f"❌ Error updating issue: {e}"


@tool("get_project_status")
async def get_project_status_tool() -> str:
    """
    Get the current status of the Production-Grade System Implementation project.
    
    Returns progress metrics including:
    - Total tasks
    - Completed tasks
    - Open tasks
    - Critical tasks
    - Progress percentage
    
    Use this to check project health and track implementation progress.
    """
    try:
        client = get_github_client()
        status = await client.get_project_status()
        
        if not status.get("success"):
            return f"❌ Failed to get project status: {status.get('error', 'Unknown error')}"
        
        return f"""📊 **Production-Grade System Implementation Status**

**Progress**: {status['progress_percentage']}% complete
- ✅ Completed: {status['completed_tasks']} tasks
- 🔄 In Progress: {status['open_tasks']} tasks
- 🚨 Critical: {status['critical_tasks']} tasks
- 📋 Total: {status['total_tasks']} tasks

**Status**: {status['status'].replace('_', ' ').title()}
"""
    except Exception as e:
        logger.error(f"Error getting project status: {e}")
        return f"❌ Error getting project status: {e}"


@tool("list_my_tasks")
async def list_my_tasks_tool(
    agent_name: str,
    state: str = "open",
) -> str:
    """
    List GitHub issues assigned to you (Elena or Marcus).
    
    Use this to see your assigned tasks and track your work.
    
    Args:
        agent_name: "Elena" or "Marcus" (to map to GitHub username)
        state: "open" or "closed" (default: "open")
        
    Returns:
        List of assigned issues with numbers and titles
    """
    try:
        client = get_github_client()
        
        # Map agent names to GitHub usernames (can be configured)
        # For now, use labels to identify agent assignments
        agent_labels = {
            "Elena": "owner:elena",
            "Marcus": "owner:marcus",
        }
        
        # Use label-based filtering since we can't easily map to usernames
        labels = ["production-grade-system"]
        if agent_name in agent_labels:
            labels.append(agent_labels[agent_name])
        
        issues = await client.list_issues(
            labels=labels,
            state=state,
        )
        
        if not issues:
            return f"📋 No {state} tasks found for {agent_name}."
        
        formatted = []
        for issue in issues[:20]:  # Limit to 20
            formatted.append(
                f"- [#{issue['number']}]({issue['html_url']}) {issue['title']}"
            )
        
        return f"📋 **{agent_name}'s Tasks** ({len(issues)} {state}):\n\n" + "\n".join(formatted)
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return f"❌ Error listing tasks: {e}"


@tool("close_task")
async def close_task_tool(issue_number: int, completion_note: Optional[str] = None) -> str:
    """
    Close a completed GitHub issue/task.
    
    Use this when you've completed a task to mark it as done.
    
    Args:
        issue_number: GitHub issue number to close
        completion_note: Optional note about completion (will be added to issue body)
        
    Returns:
        Success message or error
    """
    try:
        client = get_github_client()
        
        # Add completion note if provided
        body_update = None
        if completion_note:
            body_update = f"\n\n---\n**Completed**: {completion_note}"
        
        result = await client.update_issue(
            issue_number=issue_number,
            state="closed",
            body=body_update,
        )
        
        if result["success"]:
            return f"✅ Closed issue #{issue_number}: {result.get('issue_url', '')}"
        else:
            return f"❌ Failed to close issue: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        logger.error(f"Error closing issue: {e}")
        return f"❌ Error closing issue: {e}"

