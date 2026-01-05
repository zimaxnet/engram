---
layout: default
title: Home
nav_order: 1
description: "Engram Context Engineering Platform - Enterprise AI Memory & Cognition"
permalink: /
---

# Engram Context Engineering Platform

> **Cognition-as-a-Service for the Enterprise**

![Engram Platform Architecture](assets/images/engram-platform-architecture.png)

## Overview

Engram is an enterprise-grade AI platform that solves the **Memory Wall Problem** in Large Language Models through innovative context engineering. Built on the **Brain + Spine** architecture pattern, Engram provides durable, scalable, and cost-effective AI agent orchestration.

## Documentation Structure

### [Strategy](00-strategy/)

Executive summaries, business plans, and product roadmap.

- [AI Periodic Table](00-strategy/ai-periodic-table-roadmap.md)
- [Pricing & Deployment](00-strategy/engram-pricing-deployment-levels.md)
- [Context Engineering Research](00-strategy/Engram_Context_Engineering_GTM_Research_Paper_v2.md)

### [Architecture](01-architecture/)

System design, diagrams, and core concepts.

- [Brain + Spine Pattern](01-architecture/brain-spine-story.md)
- [4-Layer Context Schema](01-architecture/4-layer-context-schema-story.md)
- [Agent Personas](01-architecture/agents.md)
- [Memory Architecture](01-architecture/memory-architecture.md)

### [Developer Guide](02-developer/)

Setup, integration, and testing for engineers.

- [Getting Started](02-developer/getting-started/index.md)
- [IDE Integration](02-developer/ide-integration.md) (Cursor, VS Code)
- [Testing Guide](02-developer/TESTING-GUIDE.md)

### [Operations](03-operations/)

Deployment, security, and maintenance.

- [Deployment Guide](03-operations/deployment.md)
- [Enterprise Auth](03-operations/enterprise-auth-robustness-plan.md)
- [FinOps Strategy](03-operations/finops.md)

### [Features](04-features/)

Feature specifications and implementation details.

- [Voice & Chat](04-features/voice-chat-integration.md)
- [Visual Development](04-features/visual-development.md)
- [Document Ingestion](04-features/document-ingestion-strategy.md)

### [Knowledge Base](05-knowledge-base/)

Standard Operating Procedures (SOPs), troubleshooting, and historical context.

- [Azure SOPs](05-knowledge-base/azure-ai-configuration.md)
- [Troubleshooting](05-knowledge-base/chat-error-diagnosis.md)
- [Post-Mortems](05-knowledge-base/temporal-worker-postmortem.md)

---

## Agent Personas

<div class="agent-cards">
  <div class="agent-card elena">
    <img src="assets/images/elena-portrait.png" alt="Dr. Elena Vasquez" class="agent-portrait">
    <h3>Dr. Elena Vasquez</h3>
    <p class="role">Business Analyst</p>
    <p>Expert in requirements analysis and digital strategy.</p>
  </div>
  
  <div class="agent-card marcus">
    <img src="assets/images/marcus-portrait.png" alt="Marcus Chen" class="agent-portrait">
    <h3>Marcus Chen</h3>
    <p class="role">Project Manager</p>
    <p>Specialist in program management and execution.</p>
  </div>
</div>

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19 + Vite |
| Backend | FastAPI + Python 3.11 |
| Agent Framework | LangGraph + Azure AI (Foundry) |
| Orchestration | Temporal |
| Memory | Zep + Graphiti |
| Infrastructure | Azure Container Apps |
| Authentication | Microsoft Entra ID |

---

<p class="footer-note">
  Built with ❤️ using the <strong>Context Engineering</strong> paradigm
</p>
