---
layout: default
title: 4-Layer Context Schema
---

# [Home](/) › [Architecture](../) › 4-Layer Context Schema

# 4-Layer Enterprise Context Schema

The **4-Layer Enterprise Context Schema** is an Engram-original architecture pattern designed to solve the fundamental problem of stateless AI.

## Overview

Every interaction in Engram flows through a structured context object with four layers:

| Layer | Question | System Component |
|-------|----------|------------------|
| **Layer 1: Security** | WHO is making the request? WHAT can they access? | Azure Entra ID + RBAC |
| **Layer 2: Episodic** | WHAT happened recently in this conversation? | Rolling window + summary |
| **Layer 3: Semantic** | WHAT do we know from long-term memory? | Zep knowledge graph |
| **Layer 4: Operational** | WHAT are we doing right now? | Temporal workflow state |

## Documentation

- [4-Layer Context Schema Story](4-layer-context-schema-story.md) - Complete guide with examples
- [Security Context Architecture](security-context-enterprise-architecture.md) - Enterprise identity & attribution
- [Context Schema Diagram](4-layer-context-schema-diagram.json) - Visual diagram

## Layer Details

### Layer 1: SecurityContext
**Identity & Permissions**
- `user_id`, `tenant_id`, `session_id`
- `roles`, `scopes`
- `email`, `display_name`

**Why**: Multi-tenancy, RBAC enforcement, audit trail

### Layer 2: EpisodicState
**Short-Term Working Memory**
- Rolling window of recent turns
- Compressed narrative of history
- Prevents "Lost in the Middle"

**Why**: Continuity, context window management

### Layer 3: SemanticKnowledge
**Long-Term Memory Pointers**
- Facts from knowledge graph
- Entity context and relationships
- Relevance scoring

**Why**: Long-term memory, provenance, relevance

### Layer 4: OperationalState
**Workflow & Execution State**
- Temporal workflow IDs
- Plan steps and tool state
- Human-in-the-loop support
- Cost tracking

**Why**: Durable execution, cost tracking, resumability

## Enterprise Security

The SecurityContext (Layer 1) is the foundation of enterprise security:

- ✅ **Consistent Identity**: Same `user_id` across all systems
- ✅ **Enterprise Boundaries**: Tenant isolation, project scoping
- ✅ **Agent Attribution**: Marcus's work is attributable to him
- ✅ **Access Control**: Employees only see their current project data

See: [Security Context Architecture](security-context-enterprise-architecture.md)

---

**Related**: [Brain + Spine](../brain-spine/), [Authentication](../authentication/)

