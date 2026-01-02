---
layout: default
title: Engram - Context Engineering Platform
---

# Engram Context Engineering Platform

> **Cognition-as-a-Service for the Enterprise**

![Engram Platform Architecture](/assets/images/engram-platform-architecture.png)

## Overview

Engram is an enterprise-grade AI platform that solves the **Memory Wall Problem** in Large Language Models through innovative context engineering. Built on the **Brain + Spine** architecture pattern, Engram provides durable, scalable, and cost-effective AI agent orchestration.

## Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **Context Engineering** | 4-layer enterprise context schema for rich, structured AI interactions |
| 🦴 **Durable Workflows** | Temporal-based orchestration surviving crashes and enabling human-in-the-loop |
| 💾 **Temporal Knowledge Graph** | Zep + Graphiti for episodic and semantic memory |
| 🚦 **System Navigator** | Unified UI for memory exploration, workflow management, and admin oversight |
| 🎤 **Voice Interaction** | Azure VoiceLive with real-time bidirectional audio and avatar |
| 🔐 **Enterprise Security** | Entra ID authentication with fine-grained RBAC |
| 💰 **FinOps-First** | Scale-to-zero architecture minimizing costs |

## Agent Personas

Meet our AI agents:

<div class="agent-cards">
  <div class="agent-card elena">
    <img src="/assets/images/elena-portrait.png" alt="Dr. Elena Vasquez" class="agent-portrait">
    <h3>Dr. Elena Vasquez</h3>
    <p class="role">Business Analyst</p>
    <p>Expert in requirements analysis, stakeholder management, and digital transformation strategy.</p>
  </div>
  
  <div class="agent-card marcus">
    <img src="/assets/images/marcus-portrait.png" alt="Marcus Chen" class="agent-portrait">
    <h3>Marcus Chen</h3>
    <p class="role">Project Manager</p>
    <p>Specialist in program management, Agile transformation, and enterprise delivery.</p>
  </div>
</div>

## Architecture Highlights

### Brain + Spine Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                        ENGRAM PLATFORM                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   BRAIN     │    │   SPINE     │    │   MEMORY    │     │
│  │  (LangGraph)│◄──►│  (Temporal) │◄──►│    (Zep)    │     │
│  │   Agents    │    │  Workflows  │    │   Graphiti  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│              ┌─────────────┴─────────────┐                  │
│              │    4-Layer Context        │                  │
│              │  ┌──────────────────────┐ │                  │
│              │  │ 1. Security Context  │ │                  │
│              │  │ 2. Episodic State    │ │                  │
│              │  │ 3. Semantic Knowledge│ │                  │
│              │  │ 4. Operational State │ │                  │
│              │  └──────────────────────┘ │                  │
│              └───────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Voice Interaction Flow

![Voice Interaction Flow](/assets/images/voice-interaction-flow.png)

## Documentation Structure

### 🚀 Getting Started

- [Getting Started Guide](getting-started/) - Quick start and setup
- [Local Development](LOCAL-TESTING-GUIDE.md) - Local environment setup

### 🏗️ Architecture

- [Architecture Overview](architecture/) - Brain + Spine pattern
- [4-Layer Context Schema](architecture/context-schema/) - Context engineering
- [Security Context](architecture/context-schema/security-context-enterprise-architecture.md) - Enterprise security
- [Authentication](architecture/authentication/) - Auth & security architecture

### 🤖 Agents

- [Agent Personas](agents/) - Elena, Marcus, and Sage
- [Elena - Business Analyst](agents/elena/persona.md)
- [Marcus - Project Manager](agents/marcus/persona.md)

### ⚡ Features

- [Voice & Chat](features/voice/) - Voice interaction features
- [Memory & Knowledge](features/memory/) - Memory architecture
- [Connectors](features/connectors/) - Data ingestion
- [📄 Document Ingestion](document-ingestion-strategy.md) - Tri-search enterprise pipeline

### 💻 Development

- [Development Guide](development/) - Contributing to Engram
- [Testing Guide](TESTING-GUIDE.md) - Testing documentation
- [Visual Development](visual-development.md) - Creating visuals

### 🚀 Deployment

- [Deployment Guide](deployment/) - Production deployment
- [Enterprise Deployment](deployment/enterprise/) - Enterprise setup
- [FinOps Strategy](deployment/finops/) - Cost optimization

### 🔧 Operations

- [Operations Guide](operations/) - Monitoring and maintenance
- [Troubleshooting](operations/troubleshooting/) - Common issues and solutions

### 📚 Reference

- [Standard Operating Procedures](reference/sop/) - Configuration SOPs
- [API Reference](reference/api/) - API documentation

## Getting Started

```bash
# Clone the repository
git clone https://github.com/zimaxnet/engram.git

# Start local development
docker-compose up -d

# Access the platform
open http://localhost:5173
```

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
| Observability | OpenTelemetry + App Insights |

---

<p class="footer-note">
  Built with ❤️ using the <strong>Context Engineering</strong> paradigm
</p>
