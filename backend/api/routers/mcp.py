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
from backend.memory import enrich_context, persist_conversation, search_memory as mem_search
from backend.validation import validation_service
from backend.bau import bau_service
from backend.orchestration import workflow_service
from backend.etl import ingestion_service

logger = logging.getLogger(__name__)

# Initialize FastMCP server
# Note: FastMCP 0.1.0+ validates Host header. "localhost" is default in dev.
# For production (Azure Container Apps + SWA), we must allow our domains.
mcp_server = FastMCP(
    "Engram MCP Server",
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
    Search the semantic memory (RAG) for relevant facts and episodes.
    
    Args:
        query: The search query.
        session_id: Optional session ID context.
    """
    try:
        # 1. Security Context (Simulated for MCP)
        security = SecurityContext(
            user_id="mcp-user", 
            tenant_id="mcp-tenant", 
            roles=[Role.ANALYST], 
            scopes=["*"]
        )
        
        # 2. Perform Search
        results = await mem_search(query, security)
        
        # 3. Format Results
        if not results:
            return "No relevant memories found."
            
        formatted = "\n".join([f"- [{r.node_type}] {r.content} (Confidence: {r.confidence:.2f})" for r in results[:5]])
        return f"Found relevant memories:\n{formatted}"
        
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        return f"Error searching memory: {str(e)}"


@mcp_server.tool()
async def run_golden_thread(dataset_id: str = "cogai-thread", mode: str = "deterministic") -> str:
    """
    Run the Golden Thread validation suite to verify system integrity.
    
    Args:
        dataset_id: The ID of the dataset to run (default: 'cogai-thread').
        mode: Execution mode, 'deterministic' (mock) or 'acceptance' (real).
    """
    try:
        run = await validation_service.run_golden_thread(dataset_id, mode)
        return (
            f"Golden Thread Run Complete.\n"
            f"Run ID: {run.summary.run_id}\n"
            f"Status: {run.summary.status}\n"
            f"Passed: {run.summary.checks_passed}/{run.summary.checks_total}\n"
            f"Link: /validation/runs/{run.summary.run_id}"
        )
    except Exception as e:
        return f"Failed to run Golden Thread: {str(e)}"


@mcp_server.tool()
async def list_bau_flows() -> str:
    """
    List available Business As Usual (BAU) workflows.
    """
    try:
        flows = await bau_service.list_flows()
        formatted = "\n".join([f"- [{f.id}] {f.title}: {f.description}" for f in flows])
        return f"Available BAU Flows:\n{formatted}"
    except Exception as e:
        return f"Error listing BAU flows: {str(e)}"


@mcp_server.tool()
async def start_bau_flow(flow_id: str, initial_message: Optional[str] = None) -> str:
    """
    Start a specific BAU workflow.
    
    Args:
        flow_id: The ID of the flow to start (get from list_bau_flows).
        initial_message: Optional initial input for the flow.
    """
    try:
        result = await bau_service.start_flow(flow_id, initial_message)
        return (
            f"BAU Flow Started.\n"
            f"Workflow ID: {result.workflow_id}\n"
            f"Session ID: {result.session_id}\n"
            f"Initial Response: {result.message}"
        )
    except Exception as e:
        return f"Failed to start flow {flow_id}: {str(e)}"


@mcp_server.tool()
async def trigger_ingestion(source_name: str, kind: str = "Upload", url: Optional[str] = None) -> str:
    """
    Trigger a new data ingestion/ETL source.
    
    Args:
        source_name: Name for the source.
        kind: Type of source ('Upload', 'S3', 'SharePoint', 'Web').
        url: URL or path for the source (optional for Upload).
    """
    try:
        # Security stub
        security = SecurityContext(user_id="mcp-user", tenant_id="mcp-tenant", roles=[Role.ADMIN], scopes=["*"])
        
        source = await ingestion_service.create_source({
            "name": source_name,
            "kind": kind,
            "config": {"url": url} if url else {}
        }, security)
        
        return f"Ingestion Source Created: {source.id} (Status: {source.status})"
    except Exception as e:
        return f"Failed to trigger ingestion: {str(e)}"


@mcp_server.tool()
async def get_workflow_status(workflow_id: str) -> str:
    """
    Get the status of a Temporal workflow.
    
    Args:
        workflow_id: The ID of the workflow to check.
    """
    try:
        wf = await workflow_service.get_workflow(workflow_id)
        return (
            f"Workflow: {workflow_id}\n"
            f"Type: {wf.workflow_type}\n"
            f"Status: {wf.status}\n"
            f"Step: {wf.current_step}\n"
            f"Summary: {wf.task_summary}"
        )
    except Exception as e:
        return f"Error getting workflow status: {str(e)}"


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


