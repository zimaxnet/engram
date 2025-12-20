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

from backend.context.store import store as context_store
from backend.context.registry import ContextRegistry
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

@mcp_server.tool()
async def list_contexts() -> str:
    """
    List all available Virtual Context Definitions.
    """
    definitions = ContextRegistry.list()
    if not definitions:
        return "No contexts registered."
    
    formatted = "\n".join([f"- **{d.name}**: {d.description} (Params: {list(d.parameters.keys())})" for d in definitions])
    return f"Available Contexts:\n{formatted}"


@mcp_server.tool()
async def get_context(name: str, params: Optional[str] = None) -> str:
    """
    Fetch a specific Virtual Context by name.
    
    Args:
        name: The name of the context (e.g. 'project_status').
        params: JSON string of parameters to pass to the context.
    """
    import json
    try:
        parsed_params = {}
        if params:
            parsed_params = json.loads(params)
        
        result = await context_store.get_context(name, parsed_params)
        return f"Context '{name}':\n{result}"
    except Exception as e:
        return f"Error fetching context '{name}': {str(e)}"


# Dynamic Resource for reading contexts directly via URI
# Format: context://{name}?param1=val1... (Simplified to just name for now for basic resource read)
@mcp_server.resource("context://{name}")
async def read_context_resource(name: str) -> str:
    """
    Read a context definition as a resource.
    Note: Resources are typically static or parameter-less reads. 
    For parameterized reads, use the 'get_context' tool.
    This resource read will invoke the context with default/empty parameters.
    """
    try:
        result = await context_store.get_context(name, {})
        return str(result)
    except Exception as e:
        return f"Error reading context resource '{name}': {str(e)}"


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
    from backend.memory.client import memory_client
    
    try:
        # Use session_id or default to a search session
        search_session = session_id or "global-search"
        
        # Direct search via production Zep REST API
        results = await memory_client.search_memory(search_session, query, limit=10)
        
        # Format Results
        if not results:
            return "No relevant memories found."
        
        # Convert results to formatted output
        formatted_parts = []
        for r in results[:5]:
            content = r.get("content", "")[:200]
            score = r.get("score", 0.5)
            sess = r.get("session_id", "unknown")
            formatted_parts.append(f"- [{sess}] {content}... (Score: {score:.2f})")
        
        return f"Found {len(results)} relevant memories:\n" + "\n".join(formatted_parts)
        
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


# =============================================================================
# Memory Ingestion Tools - Live document and episode ingestion via MCP
# =============================================================================

@mcp_server.tool()
async def ingest_document(
    content: str,
    title: str,
    doc_type: str = "markdown",
    topics: Optional[str] = None,
    agent_id: str = "elena",
    metadata: Optional[str] = None,
) -> str:
    """
    Ingest a document into the knowledge graph.
    
    This creates searchable semantic memory that agents can reference.
    Documents become part of the shared knowledge base.
    
    Args:
        content: The full document content (markdown, text, or HTML).
        title: Document title for identification.
        doc_type: Type of document ('markdown', 'html', 'text').
        topics: Comma-separated topics (e.g., 'Architecture,Deployment').
        agent_id: Agent that primarily owns this knowledge ('elena', 'marcus').
        metadata: Optional JSON string with additional metadata.
    """
    import json
    from backend.memory.client import ZepMemoryClient
    
    try:
        # Parse metadata if provided
        doc_metadata = json.loads(metadata) if metadata else {}
        topic_list = [t.strip() for t in topics.split(",")] if topics else []
        
        # Create a unique session ID for this document
        doc_session_id = f"doc-{title.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        
        # Build messages representing the document content
        # Chunk content if very large (Zep has message limits)
        chunk_size = 4000  # Characters per chunk
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        messages = []
        for i, chunk in enumerate(chunks):
            messages.append({
                "role": "user",
                "content": f"[Document: {title} - Part {i+1}/{len(chunks)}]\n\n{chunk}",
                "metadata": {"doc_type": doc_type, "chunk": i+1, "total_chunks": len(chunks)}
            })
            messages.append({
                "role": "assistant", 
                "content": f"Acknowledged. I've indexed part {i+1} of '{title}' into my knowledge base.",
                "metadata": {"agent_id": agent_id}
            })
        
        # Create session and add to Zep
        client = ZepMemoryClient()
        await client.get_or_create_session(
            session_id=doc_session_id,
            user_id="system-ingestion",
            metadata={
                "summary": f"Document ingestion: {title}",
                "topics": topic_list,
                "agent_id": agent_id,
                "doc_type": doc_type,
                "source": "mcp_ingest_document",
                **doc_metadata
            }
        )
        
        await client.add_memory(
            session_id=doc_session_id,
            messages=messages,
            metadata={"ingested_at": str(uuid.uuid4())}  # Unique marker
        )
        
        logger.info(f"Ingested document '{title}' ({len(chunks)} chunks) → session {doc_session_id}")
        return f"✅ Ingested '{title}' ({len(content)} chars, {len(chunks)} chunks) into knowledge graph. Session: {doc_session_id}"
        
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        return f"❌ Error ingesting document: {str(e)}"


@mcp_server.tool()
async def ingest_episode(
    session_id: str,
    summary: str,
    messages: str,
    topics: Optional[str] = None,
    agent_id: str = "elena",
) -> str:
    """
    Ingest a historical episode (conversation) into episodic memory.
    
    Episodes are conversation sessions that become part of the agents'
    long-term memory. They're used to maintain context across sessions.
    
    Args:
        session_id: Unique identifier for this episode (e.g., 'sess-arch-001').
        summary: Brief summary of the episode.
        messages: JSON array of messages: [{"role": "user/assistant", "content": "...", "agent_id": "elena"}]
        topics: Comma-separated topics (e.g., 'Architecture,Zep').
        agent_id: Primary agent for this episode ('elena', 'marcus').
    """
    import json
    from backend.memory.client import ZepMemoryClient
    
    try:
        # Parse messages JSON
        message_list = json.loads(messages)
        topic_list = [t.strip() for t in topics.split(",")] if topics else []
        
        # Validate message format
        for msg in message_list:
            if "role" not in msg or "content" not in msg:
                return "❌ Invalid message format. Each message needs 'role' and 'content'."
        
        # Format messages for Zep
        formatted_messages = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "metadata": {"agent_id": msg.get("agent_id", agent_id)}
            }
            for msg in message_list
        ]
        
        # Create session and add to Zep
        client = ZepMemoryClient()
        await client.get_or_create_session(
            session_id=session_id,
            user_id="user-derek",  # Default user for project history
            metadata={
                "summary": summary,
                "topics": topic_list,
                "agent_id": agent_id,
                "turn_count": len(message_list),
                "source": "mcp_ingest_episode",
            }
        )
        
        await client.add_memory(
            session_id=session_id,
            messages=formatted_messages,
        )
        
        logger.info(f"Ingested episode '{session_id}' ({len(message_list)} messages)")
        return f"✅ Ingested episode '{session_id}' ({len(message_list)} messages). Topics: {topic_list}"
        
    except json.JSONDecodeError as e:
        return f"❌ Invalid JSON in messages: {str(e)}"
    except Exception as e:
        logger.error(f"Episode ingestion failed: {e}")
        return f"❌ Error ingesting episode: {str(e)}"


# =============================================================================
# MCP Resource: docs:// - Read documents from docs folder
# =============================================================================

@mcp_server.resource("docs://{path}")
async def read_doc_resource(path: str) -> str:
    """
    Read a document from the docs folder.
    
    This MCP resource exposes project documentation for agents and clients.
    """
    import os
    from pathlib import Path
    
    # Determine docs folder path (relative to project root)
    # In container: /app/docs, locally: {project}/docs
    docs_paths = [
        Path("/app/docs"),
        Path(__file__).parent.parent.parent.parent / "docs",  # backend/../docs
    ]
    
    docs_dir = None
    for p in docs_paths:
        if p.exists():
            docs_dir = p
            break
    
    if not docs_dir:
        return "Error: docs folder not found"
    
    # Security: prevent path traversal
    safe_path = Path(path).name if "/" not in path else path.replace("..", "")
    target = docs_dir / safe_path
    
    if not target.exists():
        return f"Error: Document '{path}' not found"
    
    if not target.is_file():
        # If it's a directory, list contents
        contents = [f.name for f in target.iterdir()]
        return f"Directory '{path}' contains: {', '.join(contents)}"
    
    try:
        return target.read_text()
    except Exception as e:
        return f"Error reading '{path}': {str(e)}"


