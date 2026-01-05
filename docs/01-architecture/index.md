---
layout: default
title: "Architecture"
nav_order: 2
has_children: true
---




# Engram Architecture

Engram implements a **Brain + Spine** architecture pattern, separating cognitive reasoning (Brain) from durable execution (Spine), with a persistent memory layer providing long-term knowledge storage.

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

## Architecture Components

### 🧠 Brain + Spine Pattern

- [Brain + Spine Story](brain-spine/brain-spine-story.md) - The foundational architecture pattern
- [Brain + Spine Diagram](brain-spine/brain-spine-diagram.json) - Visual representation

### 📋 4-Layer Context Schema

- [Context Schema Story](context-schema/4-layer-context-schema-story.md) - Complete guide to the 4-layer schema
- [Security Context Architecture](context-schema/security-context-enterprise-architecture.md) - Enterprise identity & attribution
- [Context Schema Diagram](context-schema/4-layer-context-schema-diagram.json) - Visual diagram

### 🔐 Authentication & Security

- [Authentication Analysis](authentication/authentication-analysis.md) - Authentication deep dive
- [Enterprise Auth Strategy](authentication/enterprise-auth-strategy.md) - Production authentication
- [Entra External ID](authentication/entra-external-id.md) - Azure CIAM integration
- [Authentication Flow Diagrams](authentication/diagrams/) - Visual flows

## Architecture Highlights

### Temporal Workflow Execution

![Temporal Workflow](/assets/images/temporal-workflow.png)

### Layer 1: Security Context

**SecurityContext** is the foundation of enterprise security:

- **Identity**: `user_id`, `tenant_id`, `email`, `display_name`
- **Permissions**: `roles`, `scopes`
- **Enterprise Boundaries**: Tenant isolation, project scoping, RBAC

See: [Security Context Architecture](context-schema/security-context-enterprise-architecture.md)

### Layer 2: Episodic State

Short-term working memory:

- Rolling window of recent turns
- Compressed narrative of history
- Prevents "Lost in the Middle" problem

### Layer 3: Semantic Knowledge

Long-term memory pointers:

- Facts from knowledge graph
- Entity context and relationships
- Relevance scoring

### Layer 4: Operational State

Workflow & execution state:

- Temporal workflow IDs
- Plan steps and tool state
- Human-in-the-loop support
- Cost tracking

## Related Documentation

- [Brain + Spine Pattern](brain-spine/) - Core architecture
- [Context Schema](context-schema/) - 4-layer context engineering
- [Authentication](authentication/) - Security architecture
- [Features](../features/) - Feature-specific architecture

---

**Next**: Learn about [Agent Personas](../agents/) or explore [Features](../features/).
