"""
Tool Endpoints for Foundry Agents

Provides HTTP endpoints that Foundry agents can call when using tools.
These endpoints wrap Engram's existing tool implementations.

When a Foundry agent uses a tool, Foundry will call these endpoints
with the tool name and arguments.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolRequest(BaseModel):
    """Request from Foundry agent to execute a tool."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")
    thread_id: Optional[str] = Field(None, description="Foundry thread ID")
    run_id: Optional[str] = Field(None, description="Foundry run ID")


class ToolResponse(BaseModel):
    """Response from tool execution."""
    result: str = Field(..., description="Tool execution result")
    success: bool = Field(True, description="Whether tool execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post("/{tool_name}", response_model=ToolResponse)
async def execute_tool(
    tool_name: str,
    request: ToolRequest,
    user: SecurityContext = Depends(get_current_user),
):
    """
    Execute a tool on behalf of a Foundry agent.
    
    This endpoint is called by Foundry when an agent uses a tool.
    Tools are routed to their respective implementations.
    """
    logger.info(f"Tool execution request: {tool_name} from thread {request.thread_id}")
    
    # Route to appropriate tool implementation
    try:
        if tool_name == "send_email":
            result = await _execute_send_email(request.arguments)
        elif tool_name == "list_emails":
            result = await _execute_list_emails(request.arguments)
        elif tool_name == "list_onedrive_files":
            result = await _execute_list_onedrive_files(request.arguments)
        elif tool_name == "save_to_onedrive":
            result = await _execute_save_to_onedrive(request.arguments)
        elif tool_name == "search_memory":
            result = await _execute_search_memory(request.arguments)
        elif tool_name == "analyze_requirements":
            result = await _execute_analyze_requirements(request.arguments)
        elif tool_name == "stakeholder_mapping":
            result = await _execute_stakeholder_mapping(request.arguments)
        elif tool_name == "create_user_story":
            result = await _execute_create_user_story(request.arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return ToolResponse(result=result, success=True)
        
    except Exception as e:
        logger.error(f"Tool execution failed: {tool_name}: {e}", exc_info=True)
        return ToolResponse(
            result="",
            success=False,
            error=str(e),
        )


# =============================================================================
# Microsoft Graph Tools
# =============================================================================

async def _execute_send_email(arguments: dict) -> str:
    """Execute send_email tool."""
    from backend.agents.elena.agent import send_email_tool
    
    to = arguments.get("to", "")
    subject = arguments.get("subject", "")
    body = arguments.get("body", "")
    
    if not to or not subject or not body:
        raise ValueError("Missing required arguments: to, subject, body")
    
    return await send_email_tool(to=to, subject=subject, body=body)


async def _execute_list_emails(arguments: dict) -> str:
    """Execute list_emails tool."""
    from backend.agents.elena.agent import list_emails_tool
    
    folder = arguments.get("folder", "inbox")
    limit = arguments.get("limit", 5)
    
    return await list_emails_tool(folder=folder, limit=limit)


async def _execute_list_onedrive_files(arguments: dict) -> str:
    """Execute list_onedrive_files tool."""
    from backend.agents.elena.agent import list_onedrive_files_tool
    
    folder_path = arguments.get("folder_path", "/")
    
    return await list_onedrive_files_tool(folder_path=folder_path)


async def _execute_save_to_onedrive(arguments: dict) -> str:
    """Execute save_to_onedrive tool."""
    from backend.agents.elena.agent import save_to_onedrive_tool
    
    file_path = arguments.get("file_path", "")
    content = arguments.get("content", "")
    
    if not file_path or not content:
        raise ValueError("Missing required arguments: file_path, content")
    
    return await save_to_onedrive_tool(file_path=file_path, content=content)


# =============================================================================
# Memory Tools
# =============================================================================

async def _execute_search_memory(arguments: dict) -> str:
    """Execute search_memory tool."""
    from backend.agents.elena.agent import search_memory_tool
    
    query = arguments.get("query", "")
    limit = arguments.get("limit", 5)
    
    if not query:
        raise ValueError("Missing required argument: query")
    
    return await search_memory_tool(query=query, limit=limit)


# =============================================================================
# Business Analyst Tools
# =============================================================================

async def _execute_analyze_requirements(arguments: dict) -> str:
    """Execute analyze_requirements tool."""
    from backend.agents.elena.agent import analyze_requirements
    
    requirements_text = arguments.get("requirements_text", "")
    
    if not requirements_text:
        raise ValueError("Missing required argument: requirements_text")
    
    return analyze_requirements(requirements_text=requirements_text)


async def _execute_stakeholder_mapping(arguments: dict) -> str:
    """Execute stakeholder_mapping tool."""
    from backend.agents.elena.agent import stakeholder_mapping
    
    project_name = arguments.get("project_name", "")
    stakeholders = arguments.get("stakeholders", [])
    
    if not project_name:
        raise ValueError("Missing required argument: project_name")
    
    return stakeholder_mapping(project_name=project_name, stakeholders=stakeholders)


async def _execute_create_user_story(arguments: dict) -> str:
    """Execute create_user_story tool."""
    from backend.agents.elena.agent import create_user_story
    
    title = arguments.get("title", "")
    description = arguments.get("description", "")
    acceptance_criteria = arguments.get("acceptance_criteria", [])
    
    if not title or not description:
        raise ValueError("Missing required arguments: title, description")
    
    return create_user_story(
        title=title,
        description=description,
        acceptance_criteria=acceptance_criteria,
    )

