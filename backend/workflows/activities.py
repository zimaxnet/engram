"""
Temporal Activities

Activities are the atomic units of work in Temporal workflows.
They encapsulate operations that may fail and need retry logic:
- LLM calls
- Memory operations
- External API calls
- Tool execution

Activities run in workers and can be retried automatically by Temporal.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from temporalio import activity

logger = logging.getLogger(__name__)


# =============================================================================
# Activity Input/Output Types
# =============================================================================

@dataclass
class ReasoningInput:
    """Input for the reasoning activity"""
    context_json: str  # Serialized EnterpriseContext
    user_message: str
    agent_id: str


@dataclass
class ReasoningOutput:
    """Output from the reasoning activity"""
    response: str
    context_json: str  # Updated serialized context
    tokens_used: int
    success: bool
    error: Optional[str] = None


@dataclass
class MemoryEnrichInput:
    """Input for memory enrichment"""
    context_json: str
    query: str


@dataclass
class MemoryEnrichOutput:
    """Output from memory enrichment"""
    context_json: str
    facts_retrieved: int
    entities_retrieved: int
    success: bool
    error: Optional[str] = None


@dataclass
class MemoryPersistInput:
    """Input for memory persistence"""
    context_json: str


@dataclass
class MemoryPersistOutput:
    """Output from memory persistence"""
    success: bool
    error: Optional[str] = None


@dataclass
class ToolExecutionInput:
    """Input for tool execution"""
    tool_name: str
    tool_args: dict
    context_json: str


@dataclass
class ToolExecutionOutput:
    """Output from tool execution"""
    result: str
    success: bool
    error: Optional[str] = None


# =============================================================================
# Activities
# =============================================================================

@activity.defn
async def initialize_context_activity(
    user_id: str,
    tenant_id: str,
    session_id: str,
    agent_id: str
) -> str:
    """
    Initialize a new EnterpriseContext for a workflow.
    
    This is the first activity in any agent workflow.
    Creates the security context and sets up the session.
    
    Returns:
        Serialized EnterpriseContext JSON
    """
    activity.logger.info(f"Initializing context for user {user_id}, session {session_id}")
    
    from backend.core import Role, SecurityContext, EnterpriseContext
    
    # Create security context
    security = SecurityContext(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        roles=[Role.ANALYST],  # Default role
        scopes=["*"]
    )
    
    # Create enterprise context
    context = EnterpriseContext(security=security)
    context.episodic.conversation_id = session_id
    context.operational.active_agent = agent_id
    
    return context.model_dump_json()


@activity.defn
async def enrich_memory_activity(input: MemoryEnrichInput) -> MemoryEnrichOutput:
    """
    Enrich context with relevant memory from Zep.
    
    Populates:
    - Layer 2: Episodic state (relevant past conversations)
    - Layer 3: Semantic knowledge (facts, entities from graph)
    """
    activity.logger.info(f"Enriching context with memory for query: {input.query[:50]}...")
    
    try:
        from backend.core import EnterpriseContext
        from backend.memory import enrich_context
        
        # Deserialize context
        context = EnterpriseContext.model_validate_json(input.context_json)
        
        # Enrich with memory
        context = await enrich_context(context, input.query)
        
        return MemoryEnrichOutput(
            context_json=context.model_dump_json(),
            facts_retrieved=len(context.semantic.retrieved_facts),
            entities_retrieved=len(context.semantic.entity_context),
            success=True
        )
        
    except Exception as e:
        activity.logger.error(f"Memory enrichment failed: {e}")
        return MemoryEnrichOutput(
            context_json=input.context_json,
            facts_retrieved=0,
            entities_retrieved=0,
            success=False,
            error=str(e)
        )


@activity.defn
async def agent_reasoning_activity(input: ReasoningInput) -> ReasoningOutput:
    """
    Execute agent reasoning - the core LLM call.
    
    This is the "Brain" activity - it runs the LangGraph agent
    to process the user's message and generate a response.
    """
    activity.logger.info(f"Running agent reasoning: {input.agent_id}")
    
    try:
        from backend.agents import get_agent
        from backend.core import EnterpriseContext
        
        # Deserialize context
        context = EnterpriseContext.model_validate_json(input.context_json)
        
        # Get the agent
        agent = get_agent(input.agent_id)
        
        # Run the agent
        response, updated_context = await agent.run(
            user_message=input.user_message,
            context=context
        )
        
        return ReasoningOutput(
            response=response,
            context_json=updated_context.model_dump_json(),
            tokens_used=updated_context.operational.total_tokens_used,
            success=True
        )
        
    except Exception as e:
        activity.logger.error(f"Agent reasoning failed: {e}")
        return ReasoningOutput(
            response="I apologize, but I encountered an error. Please try again.",
            context_json=input.context_json,
            tokens_used=0,
            success=False,
            error=str(e)
        )


@activity.defn
async def persist_memory_activity(input: MemoryPersistInput) -> MemoryPersistOutput:
    """
    Persist conversation to Zep memory.
    
    Called after each turn to save:
    - Episodic memory (conversation history)
    - Any new facts extracted
    """
    activity.logger.info("Persisting conversation to memory")
    
    try:
        from backend.core import EnterpriseContext
        from backend.memory import persist_conversation
        
        # Deserialize context
        context = EnterpriseContext.model_validate_json(input.context_json)
        
        # Persist to memory
        await persist_conversation(context)
        
        return MemoryPersistOutput(success=True)
        
    except Exception as e:
        activity.logger.error(f"Memory persistence failed: {e}")
        return MemoryPersistOutput(
            success=False,
            error=str(e)
        )


@activity.defn
async def execute_tool_activity(input: ToolExecutionInput) -> ToolExecutionOutput:
    """
    Execute a tool on behalf of the agent.
    
    Tools are external operations like:
    - API calls
    - Database queries
    - File operations
    - Calculations
    """
    activity.logger.info(f"Executing tool: {input.tool_name}")
    
    try:
        # Import tools from agents
        from backend.agents.elena.agent import (
            analyze_requirements,
            create_user_story,
            stakeholder_mapping,
        )
        from backend.agents.marcus.agent import (
            assess_project_risks,
            create_project_timeline,
            create_status_report,
            estimate_effort,
        )
        
        # Tool registry
        tools = {
            "analyze_requirements": analyze_requirements,
            "stakeholder_mapping": stakeholder_mapping,
            "create_user_story": create_user_story,
            "create_project_timeline": create_project_timeline,
            "assess_project_risks": assess_project_risks,
            "create_status_report": create_status_report,
            "estimate_effort": estimate_effort,
        }
        
        if input.tool_name not in tools:
            return ToolExecutionOutput(
                result="",
                success=False,
                error=f"Unknown tool: {input.tool_name}"
            )
        
        # Execute the tool
        tool = tools[input.tool_name]
        result = tool.invoke(input.tool_args)
        
        return ToolExecutionOutput(
            result=result,
            success=True
        )
        
    except Exception as e:
        activity.logger.error(f"Tool execution failed: {e}")
        return ToolExecutionOutput(
            result="",
            success=False,
            error=str(e)
        )


@activity.defn
async def send_notification_activity(
    user_id: str,
    message: str,
    notification_type: str = "info"
) -> bool:
    """
    Send a notification to the user.
    
    Used for:
    - Human-in-the-loop prompts
    - Long-running task updates
    - Error notifications
    """
    activity.logger.info(f"Sending {notification_type} notification to {user_id}")
    
    # TODO: Implement actual notification (WebSocket, email, etc.)
    # For now, just log it
    logger.info(f"NOTIFICATION [{notification_type}] to {user_id}: {message}")
    
    return True


@activity.defn
async def validate_response_activity(
    response: str,
    context_json: str
) -> tuple[bool, str]:
    """
    Validate an agent response before sending.
    
    Checks for:
    - PII exposure
    - Inappropriate content
    - Scope violations
    """
    activity.logger.info("Validating agent response")
    
    # TODO: Implement actual validation
    # - PII detection with Presidio
    # - Content moderation
    # - RBAC scope validation
    
    # For now, basic validation
    if len(response) < 10:
        return False, "Response too short"
    
    if len(response) > 10000:
        return False, "Response too long"
    
    return True, ""

