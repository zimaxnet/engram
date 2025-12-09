---
layout: default
title: Architecture
---

# Architecture Deep Dive

## Overview

The Engram platform implements a **Brain + Spine** architecture pattern, separating cognitive reasoning (Brain) from durable execution (Spine), with a persistent memory layer providing long-term knowledge storage.

![Engram Platform Architecture](/assets/images/engram-platform-architecture.png)

## Core Principles

### 1. Context Engineering over Prompt Engineering

Traditional prompt engineering focuses on crafting individual prompts. **Context Engineering** takes a holistic view:

| Aspect | Prompt Engineering | Context Engineering |
|--------|-------------------|---------------------|
| Focus | Single prompt | Full context lifecycle |
| State | Stateless | Stateful across sessions |
| Memory | Limited context window | Unlimited via external memory |
| Security | Ad-hoc | Built into context schema |

### 2. Brain + Spine Separation

| Component | Brain (LangGraph) | Spine (Temporal) |
|-----------|-------------------|------------------|
| Purpose | Reasoning & decisions | Durable execution |
| Lifecycle | Stateless functions | Long-running workflows |
| Failure | Retry at LLM level | Workflow-level recovery |
| Scale | Horizontal (replicas) | Workflow distribution |

---

## The 4-Layer Context Schema

Every interaction in Engram flows through a structured context object:

![4-Layer Context Schema](/assets/images/context-schema.svg)

### Temporal Workflow Execution

![Temporal Workflow](/assets/images/temporal-workflow.png)

### Layer 1: Security Context

```python
class SecurityContext(BaseModel):
    user_id: str           # Unique user identifier
    tenant_id: str         # Multi-tenant isolation
    roles: List[Role]      # RBAC roles (ADMIN, MANAGER, ANALYST, VIEWER)
    scopes: List[str]      # Permission scopes
    session_id: str        # Current session
```

**Purpose**: Establishes WHO is making the request and WHAT they can access.

### Layer 2: Episodic State

```python
class EpisodicState(BaseModel):
    conversation_id: str              # Current conversation
    recent_turns: List[ConvTurn]      # Recent message history
    summary: Optional[str]            # Compressed history
    last_updated_at: datetime         # Freshness tracking
```

**Purpose**: Captures WHAT happened in the current and recent conversations.

### Layer 3: Semantic Knowledge

```python
class SemanticKnowledge(BaseModel):
    retrieved_facts: List[Fact]       # Relevant facts from memory
    entity_context: Dict[str, Any]    # Known entities and relationships
    graph_nodes: List[GraphNode]      # Knowledge graph context
```

**Purpose**: Provides WHAT we know from long-term memory.

### Layer 4: Operational State

```python
class OperationalState(BaseModel):
    current_plan: List[str]           # Active plan steps
    active_tools: List[str]           # Available tools
    workflow_id: Optional[str]        # Temporal workflow ID
    status: str                       # Current execution status
    active_agent: Optional[str]       # Current agent (elena/marcus)
```

**Purpose**: Tracks WHAT we're doing right now.

---

## Component Architecture

### Brain Layer: LangGraph Agents

```
┌─────────────────────────────────────────────────────┐
│                    Agent Router                      │
│  ┌─────────────┐           ┌─────────────┐         │
│  │   Elena     │   ←────→  │   Marcus    │         │
│  │  (Analyst)  │  handoff  │  (Manager)  │         │
│  └─────────────┘           └─────────────┘         │
│         │                         │                 │
│         └───────────┬─────────────┘                 │
│                     │                               │
│              ┌──────┴──────┐                        │
│              │   Tools     │                        │
│              │ - analyze   │                        │
│              │ - plan      │                        │
│              │ - report    │                        │
│              └─────────────┘                        │
└─────────────────────────────────────────────────────┘
```

Each agent is a LangGraph state machine with:
- **System prompt** defining persona and expertise
- **Tools** for specialized operations
- **State management** via EnterpriseContext

### Spine Layer: Temporal Workflows

```
┌─────────────────────────────────────────────────────┐
│                AgentWorkflow                         │
├─────────────────────────────────────────────────────┤
│  1. initialize_context_activity                      │
│  2. enrich_memory_activity                          │
│  3. agent_reasoning_activity  ← Brain execution     │
│  4. validate_response_activity                      │
│  5. persist_memory_activity                         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              ConversationWorkflow                    │
├─────────────────────────────────────────────────────┤
│  - Long-running (can span days)                     │
│  - Signals: send_message, switch_agent              │
│  - Queries: get_history, get_turn_count            │
│  - Child workflows for each turn                    │
└─────────────────────────────────────────────────────┘
```

**Key Benefits**:
- Survives crashes and restarts
- Automatic retry with backoff
- Human-in-the-loop via signals
- Time-travel debugging

### Memory Layer: Zep + Graphiti

```
┌─────────────────────────────────────────────────────┐
│                    Zep Service                       │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐         ┌─────────────┐           │
│  │  Episodic   │         │  Semantic   │           │
│  │   Memory    │         │   Memory    │           │
│  │ (sessions)  │         │  (Graphiti) │           │
│  └─────────────┘         └─────────────┘           │
│         │                       │                   │
│         └───────────┬───────────┘                   │
│                     │                               │
│              ┌──────┴──────┐                        │
│              │  PostgreSQL │                        │
│              │  + pgvector │                        │
│              └─────────────┘                        │
└─────────────────────────────────────────────────────┘
```

**Episodic Memory** (Layer 2):
- Conversation history by session
- Automatic summarization
- Temporal retrieval

**Semantic Memory** (Layer 3):
- Knowledge graph via Graphiti
- Entity relationships
- Fact extraction and storage

---

## Data Flow

### Request Lifecycle

```
User Request
     │
     ▼
┌─────────────┐
│  FastAPI    │ ── Auth + RBAC
│   Gateway   │
└─────────────┘
     │
     ▼
┌─────────────┐
│  Temporal   │ ── Start workflow
│   Client    │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Worker    │ ── Execute activities
└─────────────┘
     │
     ├──► Memory Enrichment (Zep)
     │
     ├──► Agent Reasoning (LangGraph)
     │
     ├──► Response Validation
     │
     └──► Memory Persistence (Zep)
     │
     ▼
Response to User
```

### Voice Interaction Flow

![Voice Interaction Flow](/assets/images/voice-interaction-flow.png)

1. **Capture**: Browser captures audio via WebRTC
2. **Transcribe**: Azure Speech STT converts to text
3. **Process**: Agent workflow generates response
4. **Synthesize**: Azure Speech TTS with viseme data
5. **Animate**: Frontend renders avatar with lip-sync

---

## Security Architecture

### Authentication Flow

```
User ──► Entra ID ──► JWT Token ──► API Gateway ──► Validate ──► SecurityContext
```

### Authorization (RBAC)

| Resource | Admin | Manager | Analyst | Viewer |
|----------|-------|---------|---------|--------|
| Agents | CRUD + Execute | Read + Execute | Read + Execute | Read |
| Chat | CRUD + Execute | Create + Execute | Create + Execute | Read |
| Memory | CRUD + Admin | Create + Read | Create + Read | Read |
| Workflows | CRUD + Execute | CRUD + Execute | Read + Execute | Read |
| Settings | Admin | Read | Read | - |

### Tenant Isolation

- All data is tenant-scoped
- Cross-tenant access denied by default
- Admin override for platform operations

---

## Observability

### Distributed Tracing

```
Request ──► Span: API Gateway
              │
              └──► Span: Workflow Execution
                     │
                     ├──► Span: Memory Enrichment
                     │
                     └──► Span: Agent Reasoning
                            │
                            └──► Span: LLM Call
```

### Metrics Collected

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | method, path, status |
| `agent_executions_total` | Counter | agent_id, status |
| `agent_tokens_total` | Counter | agent_id, model |
| `workflow_duration_seconds` | Histogram | workflow_type |
| `memory_search_duration_seconds` | Histogram | operation |

### Log Correlation

All logs include:
- `trace_id`: OpenTelemetry trace ID
- `span_id`: Current span ID
- `user_id`: Authenticated user
- `tenant_id`: Active tenant

