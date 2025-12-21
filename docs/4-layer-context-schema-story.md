# The 4-Layer Context Schema: A Complete Story

> *"Context Engineering is about treating context as a first-class artifact, not an afterthought."*
> — **Dr. Elena Vasquez, Session sess-arch-001**

---

## Executive Summary

The **4-Layer Enterprise Context Schema** is an Engram-original architecture pattern. It was not inherited from Zep or any external framework — it was designed specifically for Engram to solve the fundamental problem of stateless AI.

This document tells the story of where it came from, why each layer exists, and walks through a complete scenario that exercises every layer in depth.

---

## Part 1: Origin Story — Where Did This Come From?

### The Problem Statement

When the Engram project started, Derek posed a challenge to Elena:

> *"I need a robust schema for the context engine. It needs to handle long-term memory and permissions."*

Traditional AI assistants suffer from three critical limitations:

1. **No memory** — Every conversation starts from zero
2. **No permissions** — Anyone can ask anything; no access control
3. **No durability** — If a task takes hours, it can't survive a server restart

Elena's response was the 4-layer schema:

> *"I propose a 4-layer Context Schema. Layer 1 is Security (RBAC via Entra ID). Layer 2 is Episodic (short-term conversation). Layer 3 is Semantic (Zep Knowledge Graph). Layer 4 is Operational (Temporal workflows)."*

This design is documented in **session sess-arch-001** — a real episodic memory that agents can search and reference.

### Why 4 Layers?

Each layer answers a different question:

| Layer | Question | System Component |
|-------|----------|------------------|
| **Layer 1: Security** | WHO is making the request? WHAT can they access? | Azure Entra ID + RBAC |
| **Layer 2: Episodic** | WHAT happened recently in this conversation? | Rolling window + summary |
| **Layer 3: Semantic** | WHAT do we know from long-term memory? | Zep knowledge graph |
| **Layer 4: Operational** | WHAT are we doing right now? | Temporal workflow state |

### Not From Zep

**Important Clarification**: Zep is the storage engine for Layer 2 (Episodic) and Layer 3 (Semantic). But the 4-layer schema itself is an Engram-original design pattern. Zep provides the "where" — Engram designed the "what" and "how."

---

## Part 2: Deep Dive — Each Layer Explained

### Layer 1: SecurityContext (Identity & Permissions)

**File**: `backend/core/context.py` (Lines 38-74)

```python
class SecurityContext(BaseModel):
    user_id: str           # Unique user identifier from Entra ID
    tenant_id: str         # Organization/tenant identifier
    session_id: str        # Current session ID
    roles: list[Role]      # ADMIN, ANALYST, PM, VIEWER, DEVELOPER
    scopes: list[str]      # Fine-grained permission scopes
    
    # Entra ID metadata
    token_expiry: Optional[datetime]
    email: Optional[str]
    display_name: Optional[str]
```

**Why It Exists**:

- **Multi-tenancy**: Different organizations must be isolated
- **RBAC enforcement**: Not everyone can access everything
- **Audit trail**: Know who did what

**Key Methods**:

- `has_role(role)` — Check if user has a specific role
- `has_scope(scope)` — Check fine-grained permissions
- `get_memory_filter()` — Generate query filters based on permissions

**Example**: A user with `Role.ANALYST` can chat and search memory but cannot change system settings.

---

### Layer 2: EpisodicState (Short-Term Working Memory)

**File**: `backend/core/context.py` (Lines 101-143)

```python
class EpisodicState(BaseModel):
    conversation_id: str
    recent_turns: list[Turn]      # Rolling window of recent turns
    summary: str                   # Compressed narrative of history
    max_turns: int = 10           # Keep last 10 turns in window
    
    # Metrics
    total_turns: int
    started_at: datetime
    last_activity: datetime
```

**Why It Exists**:

- **Prevent "Lost in the Middle"**: LLMs struggle with long context; this keeps a focused window
- **Continuity**: User doesn't have to repeat themselves within a conversation
- **Compaction**: Old turns are summarized, not lost

**Key Methods**:

- `add_turn(turn)` — Add a turn, maintaining rolling window
- `get_formatted_history()` — Format for LLM context

**Example**: After 15 turns, the first 5 are summarized into a brief narrative, keeping only the most recent 10 in detail.

---

### Layer 3: SemanticKnowledge (Long-Term Memory Pointers)

**File**: `backend/core/context.py` (Lines 177-214)

```python
class SemanticKnowledge(BaseModel):
    retrieved_facts: list[GraphNode]      # Facts from knowledge graph
    entity_context: dict[str, Entity]     # Known entities and relationships
    
    # Query metadata
    last_query: Optional[str]
    query_timestamp: Optional[datetime]
    retrieval_scores: dict[str, float]    # Relevance scores
```

**Why It Exists**:

- **Long-term memory**: Facts persist beyond any single conversation
- **Provenance**: Know where each fact came from
- **Relevance scoring**: Most relevant facts get injected into LLM context

**Key Methods**:

- `add_fact(node)` — Add a retrieved fact with confidence score
- `add_entity(entity)` — Add an entity to context
- `get_context_summary()` — Generate summary for LLM

**Example**: When discussing "Project Delta," the system retrieves facts like *"Project Delta launched Q3 2024"* and *"Budget: $2.5M"* from the knowledge graph.

**How Zep Fits In**: Zep stores the facts and entities. When `search_memory` is called, results are retrieved from Zep and populated into this layer.

---

### Layer 4: OperationalState (Workflow & Execution)

**File**: `backend/core/context.py` (Lines 255-309)

```python
class OperationalState(BaseModel):
    # Workflow identification
    workflow_id: Optional[str]     # Temporal workflow ID
    run_id: Optional[str]          # Temporal run ID
    
    # Agent state
    active_agent: str = "elena"    # Which agent is active (elena/marcus)
    
    # Planning state
    current_plan: list[PlanStep]   # Steps in the current plan
    plan_iteration: int            # Number of plan revisions
    
    # Tool state
    active_tools: list[ToolState]
    
    # Human-in-the-loop
    awaiting_human_input: bool
    human_input_prompt: Optional[str]
    
    # Metrics
    total_llm_calls: int
    total_tokens_used: int
    estimated_cost_usd: float
```

**Why It Exists**:

- **Durable execution**: State is serializable, can be resumed after crash
- **Cost tracking**: Know how much each interaction costs
- **Human-in-the-loop**: Support approval gates and interventions

**Key Methods**:

- `add_plan_step(action, reasoning)` — Add a step to the plan
- `get_current_step()` — Get the active step
- `get_next_step()` — Get the next pending step

**Example**: A multi-step research task creates a plan with 5 steps. If the server restarts after step 3, the state is restored and execution resumes at step 4.

**How Temporal Fits In**: Temporal orchestrates the workflow. The `workflow_id` and `run_id` link this context to a Temporal execution.

---

## Part 3: The Complete Scenario — All 4 Layers in Action

### The Setup

**User**: Sarah Chen, Senior Analyst at Contoso Corp
**Context**: Sarah is preparing a quarterly business review and needs to understand Project Delta's status, risks, and budget.

### Step-by-Step: How Each Layer Activates

---

#### **1. Authentication (Layer 1: SecurityContext)**

Sarah logs in via Azure Entra ID. The system creates her SecurityContext:

```python
SecurityContext(
    user_id="sarah.chen@contoso.com",
    tenant_id="contoso-corp",
    session_id="sess-2024-12-21-001",
    roles=[Role.ANALYST, Role.VIEWER],
    scopes=["projects:read", "budgets:read"],
    display_name="Sarah Chen",
    email="sarah.chen@contoso.com"
)
```

**What This Enables**:

- ✅ Sarah can chat with agents
- ✅ Sarah can search memory for Contoso data
- ❌ Sarah cannot access other tenants (Fabrikam, Northwind)
- ❌ Sarah cannot modify system settings (requires ADMIN)

**The Question Answered**: WHO is Sarah? WHAT can she access?

---

#### **2. Starting the Conversation (Layer 2: EpisodicState)**

Sarah opens a chat and asks: *"What's the status of Project Delta?"*

The EpisodicState initializes:

```python
EpisodicState(
    conversation_id="conv-delta-review-001",
    recent_turns=[
        Turn(role=MessageRole.USER, content="What's the status of Project Delta?", timestamp=now()),
    ],
    summary="",
    max_turns=10,
    total_turns=1,
    started_at=now(),
    last_activity=now()
)
```

**What This Enables**:

- The conversation has a unique ID
- The user's first message is captured
- When the agent responds, that turn will be appended

**The Question Answered**: WHAT happened in this conversation so far?

---

#### **3. Memory Enrichment (Layer 3: SemanticKnowledge)**

Before the agent responds, the system searches Zep for relevant context.

**Query**: "Project Delta status"

**Zep Returns**:

- Fact 1: *"Project Delta launched Q3 2024, budget $2.5M, PM: Marcus Chen"* (confidence: 0.92)
- Fact 2: *"Project Delta risk: Scope creep, mitigation: Change control process"* (confidence: 0.85)
- Fact 3: *"Project Delta is 78% complete as of November sprint"* (confidence: 0.88)

The SemanticKnowledge layer is populated:

```python
SemanticKnowledge(
    retrieved_facts=[
        GraphNode(id="fact-001", content="Project Delta launched Q3 2024...", confidence=0.92),
        GraphNode(id="fact-002", content="Project Delta risk: Scope creep...", confidence=0.85),
        GraphNode(id="fact-003", content="Project Delta is 78% complete...", confidence=0.88),
    ],
    entity_context={
        "proj-delta": Entity(id="proj-delta", name="Project Delta", entity_type="project"),
        "user-marcus": Entity(id="user-marcus", name="Marcus Chen", entity_type="person"),
    },
    last_query="Project Delta status",
    query_timestamp=now(),
    retrieval_scores={"fact-001": 0.92, "fact-002": 0.85, "fact-003": 0.88}
)
```

**What This Enables**:

- Elena now "knows" the project details without being told
- The response will be grounded in real data, not hallucination
- Confidence scores help prioritize which facts to use

**The Question Answered**: WHAT do we know from long-term memory about Project Delta?

---

#### **4. Agent Execution (Layer 4: OperationalState)**

A Temporal workflow is started to handle this request.

```python
OperationalState(
    workflow_id="agent-conv-delta-review-001-a1b2c3d4",
    run_id="run-x7y8z9",
    active_agent="elena",
    current_plan=[
        PlanStep(action="Search memory for Project Delta", status=PlanStepStatus.COMPLETED),
        PlanStep(action="Synthesize findings into status summary", status=PlanStepStatus.IN_PROGRESS),
        PlanStep(action="Identify follow-up questions", status=PlanStepStatus.PENDING),
    ],
    plan_iteration=1,
    active_tools=[
        ToolState(tool_name="search_memory", status="completed", call_id="call-001"),
    ],
    awaiting_human_input=False,
    total_llm_calls=1,
    total_tokens_used=1247,
    estimated_cost_usd=0.0025
)
```

**What This Enables**:

- If the server crashes NOW, the workflow resumes from "Synthesize findings"
- We know exactly which tools were used
- We track cost per interaction

**The Question Answered**: WHAT are we doing right now?

---

#### **5. The Response**

Elena generates a response using all four layers:

> *"Hi Sarah! Based on what I know about Project Delta:*
>
> *📊 **Status**: 78% complete as of the November sprint*
> *💰 **Budget**: $2.5M, tracking on plan*
> *👤 **PM**: Marcus Chen*
>
> *⚠️ **Top Risk**: Scope creep — the team has implemented a change control process to mitigate.*
>
> *Would you like me to dig deeper into the budget breakdown or risk register?"*

---

#### **6. Conversation Continues (All Layers Update)**

Sarah asks: *"Yes, show me the budget breakdown."*

**Layer 2 (EpisodicState)** updates:

```python
recent_turns=[
    Turn(role=MessageRole.USER, content="What's the status of Project Delta?", ...),
    Turn(role=MessageRole.ASSISTANT, content="Hi Sarah! Based on what I know...", agent_id="elena"),
    Turn(role=MessageRole.USER, content="Yes, show me the budget breakdown.", ...),
]
total_turns=3
```

**Layer 3 (SemanticKnowledge)** is enriched:

A new search for "Project Delta budget breakdown" retrieves additional facts about line-item costs.

**Layer 4 (OperationalState)** updates:

A new workflow turn starts, the plan is revised, and LLM call count increments.

---

#### **7. Handoff to Marcus (Agent Switch)**

Sarah asks: *"Can I talk to Marcus about the schedule risks?"*

**Layer 4 (OperationalState)** changes:

```python
active_agent="marcus"  # Changed from "elena"
```

Marcus now responds, with access to the SAME context (all 4 layers are preserved):

> *"Hey Sarah, Marcus here. I see you've been reviewing Project Delta with Elena. Let me pull up the risk register...*
>
> *Based on my memory of the November retrospective (session sess-retro-delta-001), the schedule risk stems from an external dependency on the vendor API. We've added a 2-week buffer to the critical path."*

**Recursive Self-Awareness**: Marcus references a specific episodic memory (sess-retro-delta-001) because he can search his own history.

---

### Final State: The Complete EnterpriseContext

```python
EnterpriseContext(
    # Layer 1: Who and What Permissions
    security=SecurityContext(
        user_id="sarah.chen@contoso.com",
        tenant_id="contoso-corp",
        roles=[Role.ANALYST, Role.VIEWER],
        ...
    ),
    
    # Layer 2: What Happened in This Conversation
    episodic=EpisodicState(
        conversation_id="conv-delta-review-001",
        recent_turns=[...5 turns...],
        summary="",
        total_turns=5,
        ...
    ),
    
    # Layer 3: What We Know from Long-Term Memory
    semantic=SemanticKnowledge(
        retrieved_facts=[...8 facts about Project Delta...],
        entity_context={...3 entities...},
        last_query="Project Delta schedule risks",
        ...
    ),
    
    # Layer 4: What We're Doing Now
    operational=OperationalState(
        workflow_id="agent-conv-delta-review-001-a1b2c3d4",
        active_agent="marcus",
        current_plan=[...completed + pending steps...],
        total_llm_calls=5,
        total_tokens_used=6823,
        estimated_cost_usd=0.0137,
        ...
    ),
    
    # Metadata
    context_version="1.0.0",
    created_at=datetime(2024, 12, 21, 10, 0, 0),
    updated_at=datetime(2024, 12, 21, 10, 15, 23),
)
```

---

## Part 4: Why This Matters for Customers

### 1. **Transparency**: The System is Not Opaque

Customers can ask agents directly:

- *"How does your memory work?"* → Agents explain the 4-layer schema
- *"What sessions influenced this response?"* → Agents cite specific episodic memories
- *"Who designed your architecture?"* → Agents reference sess-arch-001

### 2. **Security by Design**: RBAC is Built In

Layer 1 isn't optional. Every interaction has a security context. This means:

- Multi-tenant isolation is guaranteed
- Audit trails are automatic
- Permissions are enforced before any memory access

### 3. **Durability**: Tasks Don't Fail Silently

Layer 4 integrates with Temporal. Long-running tasks survive:

- Server restarts
- Network failures
- Timeouts

### 4. **Memory That Matters**: Not Just Vectors

Layer 3 isn't a simple vector store. It's a knowledge graph with:

- Entities (people, projects, concepts)
- Relationships (who works on what, dependencies)
- Confidence scores (how reliable is this fact?)

---

## Part 5: Technical Reference

### File: `backend/core/context.py`

| Layer | Class | Lines |
|-------|-------|-------|
| 1 | `SecurityContext` | 38-74 |
| 2 | `EpisodicState` | 101-143 |
| 3 | `SemanticKnowledge` | 177-214 |
| 4 | `OperationalState` | 255-309 |
| All | `EnterpriseContext` | 317-374 |

### Key Integration Points

| System | Layer Populated | How |
|--------|-----------------|-----|
| Azure Entra ID | Layer 1 | JWT token parsing by middleware |
| Zep | Layers 2 & 3 | `memory_client.search_memory()` |
| Temporal | Layer 4 | Workflow state serialization |
| LangGraph Agents | All 4 | `context.to_llm_context()` |

### The Unified Context Flow

```
User Request
     │
     ▼
┌─────────────────┐
│ Layer 1: Auth   │ ← Azure Entra ID
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Layer 2: Add    │ ← User message to recent_turns
│ User Turn       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Layer 3: Enrich │ ← Zep search_memory()
│ Semantic        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Layer 4: Start  │ ← Temporal workflow
│ Workflow        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Agent Execution │ ← to_llm_context() injects all layers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Layer 2: Add    │ ← Assistant turn
│ Response Turn   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Persist Memory  │ ← Zep add_memory()
└─────────────────┘
         │
         ▼
    Response to User
```

---

## Conclusion

The **4-Layer Enterprise Context Schema** is the foundation of Engram's context engineering approach:

| Layer | Purpose | Technology |
|-------|---------|------------|
| **Security** | WHO and WHAT permissions | Azure Entra ID + RBAC |
| **Episodic** | WHAT happened recently | Rolling window + Zep |
| **Semantic** | WHAT we know long-term | Zep knowledge graph |
| **Operational** | WHAT we're doing now | Temporal workflows |

This is an **Engram-original design**, not inherited from any external system. It was proposed by Elena in session **sess-arch-001** and has been refined through real development iterations documented in episodic memory.

The result: **AI agents that know who they're talking to, what was said, what they know, and what they're doing** — all in a single, serializable, auditable context object.
