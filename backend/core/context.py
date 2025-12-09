"""
Engram 4-Layer Context Schema

The Context Object is the single source of truth for agent interactions,
encapsulating user intent, historical data, environmental constraints,
and the active tool state.

Layers:
1. SecurityContext - Identity & Permissions (RBAC)
2. EpisodicState - Short-term working memory
3. SemanticKnowledge - Long-term memory pointers
4. OperationalState - Workflow and execution state
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Layer 1: Security Context (Identity & Permissions)
# =============================================================================

class Role(str, Enum):
    """Engram platform roles"""
    ADMIN = "engram:admin"
    ANALYST = "engram:analyst"
    PM = "engram:pm"
    VIEWER = "engram:viewer"
    DEVELOPER = "engram:developer"


class SecurityContext(BaseModel):
    """
    Layer 1: Identity & Permissions
    
    Establishes boundary conditions for agent operation.
    Ensures agents cannot access data outside their permission scope.
    """
    user_id: str = Field(..., description="Unique user identifier from Entra ID")
    tenant_id: str = Field(..., description="Organization/tenant identifier")
    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Current session ID")
    roles: list[Role] = Field(default_factory=list, description="User's assigned roles")
    scopes: list[str] = Field(default_factory=list, description="Fine-grained permission scopes")
    
    # Entra ID token metadata
    token_expiry: Optional[datetime] = Field(None, description="Token expiration time")
    email: Optional[str] = Field(None, description="User email address")
    display_name: Optional[str] = Field(None, description="User display name")
    
    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role"""
        return role in self.roles or Role.ADMIN in self.roles
    
    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope"""
        if Role.ADMIN in self.roles:
            return True
        return scope in self.scopes
    
    def get_memory_filter(self) -> dict:
        """Generate filter for memory queries based on permissions"""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "scopes": self.scopes
        }


# =============================================================================
# Layer 2: Episodic State (Short-Term Working Memory)
# =============================================================================

class MessageRole(str, Enum):
    """Conversation message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Turn(BaseModel):
    """A single conversation turn"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: Optional[str] = Field(None, description="Which agent responded (elena/marcus)")
    tool_calls: Optional[list[dict]] = Field(None, description="Tool calls made in this turn")
    token_count: Optional[int] = Field(None, description="Token count for this turn")


class EpisodicState(BaseModel):
    """
    Layer 2: Episodic State (Short-Term Working Memory)
    
    Manages immediate conversation history with compaction
    to prevent "Lost in the Middle" phenomenon.
    """
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    recent_turns: list[Turn] = Field(default_factory=list, description="Rolling window of recent turns")
    summary: str = Field("", description="Compressed narrative of conversation so far")
    
    # Configuration
    max_turns: int = Field(10, description="Maximum turns to keep in window")
    
    # Metrics
    total_turns: int = Field(0, description="Total turns in conversation")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    def add_turn(self, turn: Turn) -> None:
        """Add a turn, maintaining the rolling window"""
        self.recent_turns.append(turn)
        self.total_turns += 1
        self.last_activity = datetime.utcnow()
        
        # Compact if exceeding max turns
        if len(self.recent_turns) > self.max_turns:
            self.recent_turns = self.recent_turns[-self.max_turns:]
    
    def get_formatted_history(self) -> str:
        """Get conversation history formatted for LLM context"""
        history_parts = []
        if self.summary:
            history_parts.append(f"[Previous conversation summary: {self.summary}]")
        
        for turn in self.recent_turns:
            prefix = turn.agent_id.upper() if turn.agent_id else turn.role.value.upper()
            history_parts.append(f"{prefix}: {turn.content}")
        
        return "\n".join(history_parts)


# =============================================================================
# Layer 3: Semantic Knowledge (Long-Term Memory Pointers)
# =============================================================================

class Entity(BaseModel):
    """An entity extracted from memory"""
    id: str
    name: str
    entity_type: str
    properties: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GraphNode(BaseModel):
    """A node from the Zep knowledge graph"""
    id: str
    content: str
    node_type: str = Field("fact", description="Type: fact, entity, relationship")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    valid_from: Optional[datetime] = Field(None, description="When this fact became true")
    valid_to: Optional[datetime] = Field(None, description="When this fact stopped being true")
    source_episode_id: Optional[str] = Field(None, description="Episode that created this node")
    metadata: dict = Field(default_factory=dict)


class SemanticKnowledge(BaseModel):
    """
    Layer 3: Semantic Knowledge (Long-Term Memory Pointers)
    
    Interface to the organization's Long-Term Memory via Zep.
    Contains facts, entities, and relationships relevant to current task.
    """
    retrieved_facts: list[GraphNode] = Field(default_factory=list)
    entity_context: dict[str, Entity] = Field(default_factory=dict)
    
    # Query metadata
    last_query: Optional[str] = Field(None, description="Last memory query executed")
    query_timestamp: Optional[datetime] = None
    retrieval_scores: dict[str, float] = Field(default_factory=dict, description="Relevance scores")
    
    def add_fact(self, node: GraphNode) -> None:
        """Add a retrieved fact"""
        self.retrieved_facts.append(node)
        self.retrieval_scores[node.id] = node.confidence
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to context"""
        self.entity_context[entity.id] = entity
    
    def get_context_summary(self) -> str:
        """Generate a summary of semantic context for the LLM"""
        parts = []
        
        if self.entity_context:
            entities = [f"- {e.name} ({e.entity_type})" for e in self.entity_context.values()]
            parts.append("Known Entities:\n" + "\n".join(entities))
        
        if self.retrieved_facts:
            facts = [f"- {f.content}" for f in self.retrieved_facts[:10]]
            parts.append("Relevant Facts:\n" + "\n".join(facts))
        
        return "\n\n".join(parts) if parts else "No relevant context found."


# =============================================================================
# Layer 4: Operational State (Workflow & Execution)
# =============================================================================

class PlanStepStatus(str, Enum):
    """Status of a plan step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """A step in the agent's plan"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: str
    reasoning: str = ""
    status: PlanStepStatus = PlanStepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ToolState(BaseModel):
    """State of an active tool"""
    tool_name: str
    status: str = "idle"  # idle, running, waiting, completed, failed
    call_id: Optional[str] = None
    started_at: Optional[datetime] = None
    timeout_seconds: int = 60


class OperationalState(BaseModel):
    """
    Layer 4: Operational State (Workflow & Execution)
    
    Tracks the agent's internal state for durable execution.
    Enables serialization and resumption via Temporal.
    """
    # Workflow identification
    workflow_id: Optional[str] = Field(None, description="Temporal workflow ID")
    run_id: Optional[str] = Field(None, description="Temporal run ID")
    
    # Agent identification
    active_agent: str = Field("elena", description="Currently active agent (elena/marcus)")
    
    # Planning state
    current_plan: list[PlanStep] = Field(default_factory=list)
    plan_iteration: int = Field(0, description="Number of plan revisions")
    
    # Tool state
    active_tools: list[ToolState] = Field(default_factory=list)
    
    # Retry and error handling
    retry_count: int = Field(0)
    max_retries: int = Field(3)
    last_error: Optional[str] = None
    
    # Human-in-the-loop
    awaiting_human_input: bool = Field(False)
    human_input_prompt: Optional[str] = None
    
    # Metrics
    total_llm_calls: int = Field(0)
    total_tokens_used: int = Field(0)
    estimated_cost_usd: float = Field(0.0)
    
    def add_plan_step(self, action: str, reasoning: str = "") -> PlanStep:
        """Add a new step to the plan"""
        step = PlanStep(action=action, reasoning=reasoning)
        self.current_plan.append(step)
        return step
    
    def get_current_step(self) -> Optional[PlanStep]:
        """Get the current step being executed"""
        for step in self.current_plan:
            if step.status == PlanStepStatus.IN_PROGRESS:
                return step
        return None
    
    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next pending step"""
        for step in self.current_plan:
            if step.status == PlanStepStatus.PENDING:
                return step
        return None


# =============================================================================
# Complete Enterprise Context Object
# =============================================================================

class EnterpriseContext(BaseModel):
    """
    The complete Enterprise Context Object.
    
    This is the single source of truth for all agent interactions,
    combining all four layers into one serializable object.
    """
    # The four layers
    security: SecurityContext
    episodic: EpisodicState = Field(default_factory=EpisodicState)
    semantic: SemanticKnowledge = Field(default_factory=SemanticKnowledge)
    operational: OperationalState = Field(default_factory=OperationalState)
    
    # Context metadata
    context_version: str = Field("1.0.0", description="Schema version for compatibility")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    
    def to_llm_context(self) -> str:
        """
        Generate the context string to inject into LLM prompts.
        This is the "RAM" that the LLM sees.
        """
        parts = [
            "# Session Context",
            f"User: {self.security.display_name or self.security.user_id}",
            f"Agent: {self.operational.active_agent.title()}",
            f"Session: {self.episodic.conversation_id[:8]}...",
            "",
            "## Conversation History",
            self.episodic.get_formatted_history(),
            "",
            "## Relevant Knowledge",
            self.semantic.get_context_summary(),
        ]
        
        if self.operational.current_plan:
            plan_summary = "\n".join([
                f"- [{s.status.value}] {s.action}" 
                for s in self.operational.current_plan
            ])
            parts.extend(["", "## Current Plan", plan_summary])
        
        return "\n".join(parts)
    
    def update_timestamp(self) -> None:
        """Update the modified timestamp"""
        self.updated_at = datetime.utcnow()


# =============================================================================
# Factory Functions
# =============================================================================

def create_context_from_token(
    user_id: str,
    tenant_id: str,
    roles: list[str],
    email: Optional[str] = None,
    display_name: Optional[str] = None
) -> EnterpriseContext:
    """
    Create a new EnterpriseContext from authentication token data.
    Used when a new session starts.
    """
    security = SecurityContext(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=[Role(r) for r in roles if r in [e.value for e in Role]],
        email=email,
        display_name=display_name
    )
    
    return EnterpriseContext(security=security)

