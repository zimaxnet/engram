# Engram Context Engineering Platform

> **Cognition-as-a-Service for the Enterprise**

![Engram Platform Architecture](docs/assets/images/engram-platform-architecture.png)

## Overview

Engram is an enterprise-grade AI platform that solves the **Memory Wall Problem** in Large Language Models.

[Read the Full Documentation on our Wiki](https://wiki.engram.work)

## Repository Structure

- `frontend/` - React 19 + Vite application
- `backend/` - FastAPI + LangGraph agents
- `docs/` - Jekyll Documentation Site
- `infra/` - Azure Bicep Infrastructure

## Documentation

- **[Strategy](docs/00-strategy/)**: Business plans, roadmaps
- **[Architecture](docs/01-architecture/)**: System diagrams
- **[Developer Guide](docs/02-developer/)**: Setup and testing
- **[Operations](docs/03-operations/)**: Deployment and Auth
- **[Features](docs/04-features/)**: Specs and designs
- **[Knowledge Base](docs/05-knowledge-base/)**: SOPs and Troubleshooting

## Getting Started

```bash
# Clone
git clone https://github.com/zimaxnet/engram.git

# Local Dev
docker-compose up -d
open http://localhost:5173
```
