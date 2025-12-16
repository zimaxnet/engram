"""
MCP Router for Engram

Exposes Engram context and capabilities via the Model Context Protocol (MCP).
Uses SSE (Server-Sent Events) for transport.
"""

import asyncio
import logging
import uuid
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

from backend.agents import chat as agent_chat, get_agent
from backend.core import EnterpriseContext, SecurityContext, Role
from backend.memory import enrich_context, persist_conversation

logger = logging.getLogger(__name__)

# Initialize FastMCP server
# Note: FastMCP 0.1.0+ validates Host header. "localhost" is default in dev.
# For production (Azure Container Apps + SWA), we must allow our domains.
mcp_server = FastMCP(
    "Engram MCP Server",
    dependencies=["mcp"], 
    warn_on_duplicate_resources=False
)

# Monkey-patch or configure starlette app settings if exposed directly?
# FastMCP uses Starlette internally. To fix "Invalid Host header", usually need TrustedHostMiddleware.
# Since we mount it in FastAPI, FastAPI *should* handle hosts if we didn't use .sse_app() directly.
# However, .sse_app() creates a sub-application.
# Fix: We will configure the FastMCP instance environment if possible, or
# rely on the fact that we can modify the internal Starlette app middleware *after* creation if needed.
# BETTER FIX: FastMCP doesn't expose host config easily in constructor in v0.4.0?
# Let's try adding '*' to allowed hosts if supported, or rely on X-Forwarded-Host.


# Session storage (in-memory for now, same as chat.py)
_sessions: dict[str, EnterpriseContext] = {}

def _get_or_create_session(session_id: str, security: SecurityContext) -> EnterpriseContext:
    if session_id not in _sessions:
        _sessions[session_id] = EnterpriseContext(security=security)
        _sessions[session_id].episodic.conversation_id = session_id
    return _sessions[session_id]

@mcp_server.resource("context://current")
async def get_current_context() -> str:
    """Get the current test context"""
    return "Engram MCP Context: Active"

@mcp_server.tool()
async def chat_with_agent(
    message: str, 
    session_id: Optional[str] = None, 
    agent_id: Optional[str] = "elena",
    ctx: Context = None
) -> str:
    """
    Chat with an Engram agent.
    
    Args:
        message: The user's message.
        session_id: Optional session ID. If not provided, a new one is generated.
        agent_id: The ID of the agent to chat with (default: "elena").
    """
    # 1. Setup Security Context
    # In a real scenario, we might extract this from ctx.request_context or similar if available/authenticated
    security = SecurityContext(
        user_id="mcp-user", 
        tenant_id="mcp-tenant", 
        roles=[Role.ANALYST], 
        scopes=["*"]
    )
    
    # 2. Session Management
    actual_session_id = session_id or str(uuid.uuid4())
    context = _get_or_create_session(actual_session_id, security)
    
    # 3. Enrich Context
    try:
        context = await asyncio.wait_for(
            enrich_context(context, message),
            timeout=2.0
        )
    except Exception as e:
        logger.warning(f"Memory enrichment failed: {e}")
        if ctx:
            try:
                await ctx.info(f"Memory enrichment warning: {e}")
            except Exception:
                pass

    # 4. Agent Execution
    try:
        response_text, updated_context, used_agent_id = await agent_chat(
            query=message, context=context, agent_id=agent_id
        )
        
        # 5. Update Session & Persist
        _sessions[actual_session_id] = updated_context
        
        # Fire-and-forget persistence (or await it for safety in this tool)
        # We await it here to ensure consistency for E2E tests
        try:
            await persist_conversation(updated_context)
        except Exception as e:
            logger.warning(f"Persistence failed: {e}")

        # 6. Report info to client if context available
        if ctx:
            try:
                await ctx.info(f"Agent {used_agent_id} responded in session {actual_session_id}")
            except Exception:
                pass

        return response_text

    except Exception as e:
        logger.error(f"Agent chat failed: {e}")
        return f"Error processing request: {str(e)}"


@mcp_server.tool()
async def enrich_memory(text: str, session_id: Optional[str] = None) -> str:
    """
    Enrich the context memory with new information.
    
    Args:
        text: The text to be processed and added to memory.
        session_id: Optional session ID to associate with the memory.
    """
    try:
        # Create temporary security/session context
        security = SecurityContext(
            user_id="mcp-user", 
            tenant_id="mcp-tenant", 
            roles=[Role.ANALYST], 
            scopes=["*"]
        )
        actual_session_id = session_id or str(uuid.uuid4())
        context = _get_or_create_session(actual_session_id, security)
        
        await enrich_context(context, text)
        return "Memory enriched successfully."
    except Exception as e:
        logger.error(f"Enrich memory failed: {e}")
        return f"Error enriching memory: {str(e)}"


@mcp_server.tool()
async def search_memory(query: str, session_id: Optional[str] = None) -> str:
    """
    Search the semantic memory (RAG).
    
    Args:
        query: The search query.
        session_id: Optional session ID for context-aware search.
    """
    # In a real implementation, we would expose memory.search or similar.
    # For now, we simulate or reuse enrich_context which retrieves facts.
    # A dedicated search function would be better in backend.memory.
    return f"Memory search for '{query}' initiated. (Result simulation)"


@mcp_server.tool()
async def get_voice_config(agent_id: str) -> str:
    """
    Get the voice configuration for a specific agent.
    
    Args:
        agent_id: The ID of the agent (e.g., 'elena', 'marcus').
    """
    from backend.voice.voicelive_service import voicelive_service
    try:
        config = voicelive_service.get_agent_voice_config(agent_id)
        return f"Agent: {agent_id}, Voice: {config.voice_name}, Model: {voicelive_service.model}"
    except Exception as e:
        return f"Error fetching voice config: {str(e)}"


