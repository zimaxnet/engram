---
layout: default
title: Brain + Spine Architecture
---

# [Home](/) › [Architecture](../) › Brain + Spine

# Brain + Spine Architecture

The **Brain + Spine** pattern is Engram's foundational architecture, separating cognitive reasoning from durable execution.

## Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Brain** | LangGraph | Cognitive reasoning & agent orchestration |
| **Spine** | Temporal | Durable workflow execution |
| **Memory** | Zep + Graphiti | Long-term knowledge storage |

## Documentation

- [Brain + Spine Story](brain-spine-story.md) - Complete guide to the Brain + Spine pattern
- [Brain + Spine Diagram](brain-spine-diagram.json) - Visual representation

## Key Concepts

### Brain (LangGraph)
- Stateless agent functions
- Reasoning and decision-making
- Tool orchestration
- Horizontal scaling

### Spine (Temporal)
- Long-running workflows
- Durable execution
- Human-in-the-loop
- Workflow recovery

### Memory (Zep)
- Episodic memory (conversations)
- Semantic memory (knowledge graph)
- Session management
- Search and retrieval

---

**Related**: [4-Layer Context Schema](../context-schema/), [Authentication](../authentication/)

