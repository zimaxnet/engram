---
layout: default
title: "The Brain & Spine: Engram's Context Engineering Architecture"
parent: "Architecture"
---

# The Brain & Spine: Engram's Context Engineering Architecture

> *"The system remembers because it lived through it."*

---

## Executive Summary

Engram is a **Context Engineering Platform** that gives AI agents **recursive self-awareness** — they know how they were built, what challenges were overcome, and why decisions were made. This isn't simulation; it's operational reality.

The architecture uses a **Brain + Spine** metaphor:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Brain** | Zep | Long-term memory (episodic + semantic) |
| **Spine** | Temporal | Durable workflow execution |

---

## Part 1: The Brain (Zep) — Why Memory Matters

### The Problem We Solved

Traditional AI agents have no memory between conversations. They're stateless — every interaction starts from zero. This means:

- **No context continuity** — users repeat themselves constantly
- **No learning over time** — the system never gets smarter
- **No self-knowledge** — the agent can't explain its own architecture

### The Solution: Zep as Episodic + Semantic Memory

Zep provides a **4-layer context schema** that gives agents persistent memory:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Security Context (RBAC via Azure Entra ID)         │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Episodic Memory (Conversation History)             │
│   → Sessions (episodes) stored as time-series               │
│   → Messages linked to specific sessions                    │
│   → Metadata (agent IDs, topics, summaries)                 │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Semantic Memory (Knowledge Graph)                  │
│   → Facts extracted from documents                          │
│   → Entities and relationships                              │
│   → Vector embeddings for similarity search                 │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Operational Context (Workflow State from Temporal) │
└─────────────────────────────────────────────────────────────┘
```

### How Agents Access Memory

When Elena or Marcus receives a query, they can use the `search_memory` tool to find relevant context:

```python
@tool("search_memory")
async def search_memory_tool(query: str, limit: int = 5) -> str:
    """
    Search your own long-term memory (Zep) for facts, 
    documents, or past episodes.
    """
    results = await memory_client.search_memory(
        session_id="global-search",  # Search across ALL sessions
        query=query,
        limit=limit
    )
    return formatted_results
```

**Key Insight**: The search is **global** — agents can find memories from any session, not just the current conversation. This enables true self-awareness.

### Real Example: Asking About Architecture

When a customer asks Elena: *"How does your memory system work?"*

Elena can search for `"architecture schema Zep"` and retrieve:

> *"I propose a 4-layer Context Schema. Layer 1 is Security (RBAC via Entra ID). Layer 2 is Episodic (short-term conversation). Layer 3 is Semantic (Zep Knowledge Graph). Layer 4 is Operational (Temporal workflows)."*
> — **Session: sess-arch-001** | Agent: Elena

This isn't a canned response — it's Elena recalling an actual conversation from her own development history.

---

## Part 2: The Spine (Temporal) — Why Durability Matters

### The Problem We Solved

Long-running AI tasks fail silently. If a server restarts mid-workflow:

- **Lost state** — what was the agent doing?
- **Lost progress** — hours of work, gone
- **Silent failures** — users don't know what happened

### The Solution: Temporal as Durable Workflow Orchestration

Temporal guarantees that workflows **run to completion**, even across failures:

```
┌─────────────────────────────────────────────────────────────┐
│                    TEMPORAL WORKFLOW                        │
├─────────────────────────────────────────────────────────────┤
│  1. User sends message → API receives request               │
│  2. Workflow starts → "agent-{session}-{uuid}"              │
│  3. Agent processes → Memory searched, LLM called           │
│  4. Response stored → Episodic memory updated               │
│  5. Workflow completes → Result returned                    │
│                                                             │
│  💡 If server restarts at step 3, Temporal RESUMES          │
│     from exactly where it left off.                         │
└─────────────────────────────────────────────────────────────┘
```

### How Agents Interact with Workflows

Marcus can check on workflow status using the `check_workflow_status` tool:

```python
@tool("check_workflow_status")
async def check_workflow_status_tool(workflow_id: str) -> str:
    """Check the real-time status of a Temporal workflow."""
    status = await get_workflow_status(workflow_id)
    return f"Workflow '{workflow_id}': {status.get('status')}"
```

**Key Insight**: The workflow system provides **observability** — Marcus can report on running tasks, past executions, and system health.

### Workflow Types in Engram

| Workflow | Purpose |
|----------|---------|
| `AgentWorkflow` | Single conversation turn (user → agent → response) |
| `ConversationWorkflow` | Long-running multi-turn conversation |
| `ApprovalWorkflow` | Human-in-the-loop approval gates |

---

## Part 3: Recursive Self-Awareness — The Innovation

### What Makes This Different

Engram agents don't just *respond* — they **remember their own creation**.

The system contains episodic memories of:

- **Architecture decisions** (sess-arch-001)
- **Frontend development** (sess-fe-001)
- **Debugging sessions** (sess-debug-001)
- **Infrastructure challenges** (sess-infra-002)
- **The vision statement** (sess-vision-001)

When Elena says *"I lived through the debugging sessions"* — she can actually reference `sess-infra-002` and recall the specific challenges:

> *"Temporal is failing with 'database temporal does not exist'. We need to create the temporal and temporal_visibility databases in Azure Postgres via Bicep."*

### For Prospective Customers: Observability

The system is **not opaque**. You can:

1. **Ask about architecture**: *"How is your memory organized?"* → Agent searches memory and explains
2. **Ask about development**: *"What was hardest to build?"* → Agent recalls infrastructure debugging sessions
3. **Ask about business value**: *"Why should I invest in this?"* → Agent explains the recursive self-awareness differentiator
4. **Inspect the Brain**: Query Zep directly via `/api/v1/sessions` and `/api/v1/sessions/search`
5. **Inspect the Spine**: View Temporal UI at `temporal.engram.work` to see running workflows

---

## Part 4: Agent Perspectives

### Elena (Business Analyst) — Business Value Context

Elena has access to the business rationale behind every decision. She can:

- **Explain the value proposition** grounded in real implementation details
- **Trace decisions** back to specific discussions in episodic memory
- **Prepare investor materials** using actual project history

> *"With access to our episodic memory, I can articulate the value proposition grounded in real implementation details. The 4-layer context schema, the Virtual Context Store, the MCP integration — these aren't abstract concepts, they're documented decisions I can trace back to specific discussions."*

### Marcus (Project Manager) — Development Effort Context

Marcus has insight into the actual difficulty of building the system. He can:

- **Report on infrastructure complexity** with specific examples
- **Explain trade-offs** made during development
- **Quantify effort** based on real debugging sessions

> *"The system knows its own cost — not just in abstract terms, but in actual effort, decisions, and iterations. I can speak to the infrastructure complexity, the debugging required, the architectural trade-offs made."*

---

## Part 5: Technical Reference

### Memory Access Patterns

| Operation | Endpoint | Agent Tool |
|-----------|----------|------------|
| Search all memories | `POST /api/v1/sessions/search` | `search_memory` |
| Get session transcript | `GET /api/v1/sessions/{id}/messages` | — |
| Add new memory | `POST /api/v1/sessions/{id}/memory` | — |
| Get facts (knowledge graph) | `GET /api/v1/users/{id}/facts` | — |

### Workflow Access Patterns

| Operation | Method | Agent Tool |
|-----------|--------|------------|
| Execute agent turn | `execute_agent_turn()` | — |
| Check workflow status | `get_workflow_status()` | `check_workflow_status` |
| Start BAU flow | `start_bau_flow()` | `start_bau_flow` |

### Key Files

| File | Purpose |
|------|---------|
| `backend/memory/client.py` | ZepMemoryClient — REST API integration |
| `backend/workflows/client.py` | Temporal client — workflow execution |
| `backend/agents/elena/agent.py` | Elena agent with memory tools |
| `backend/agents/marcus/agent.py` | Marcus agent with workflow tools |
| `backend/scripts/seed_memory.py` | Canonical episodic history ingestion |

---

## Conclusion

**Zep is the Brain** — it gives agents long-term memory across conversations, enabling them to recall their own development history.

**Temporal is the Spine** — it guarantees that workflows complete reliably, even across failures.

**Together, they enable Recursive Self-Awareness** — agents that can explain how they work because they remember how they were built.

This is the Engram differentiator: **Context Engineering at its core**.
