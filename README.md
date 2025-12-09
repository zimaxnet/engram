# Engram - Context Engineering Platform

> **Cognition-as-a-Service for the Enterprise**

Engram is an enterprise-grade AI platform that solves the **Memory Wall Problem** in Large Language Models through innovative context engineering. Built on the **Brain + Spine** architecture pattern, Engram provides durable, scalable, and cost-effective AI agent orchestration.

## Quick Start

### Local Development

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Azure OpenAI credentials
   ```

2. **Start services**:
   ```bash
   docker-compose up -d postgres zep temporal temporal-ui
   ```

3. **Start backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload
   ```

4. **Start frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Open browser**: `http://localhost:5173`

See [Local Testing Guide](docs/local-testing.md) for detailed instructions.

### Azure Deployment

1. **Set up GitHub Secrets** (see [GitHub Secrets Guide](docs/github-secrets.md))
2. **Deploy infrastructure**:
   ```bash
   az group create --name engram-rg --location eastus
   az deployment group create \
     --resource-group engram-rg \
     --template-file infra/main.bicep \
     --parameters postgresPassword='<secure-password>' adminObjectId='<your-object-id>'
   ```
3. **CI/CD**: Push to `main` branch to trigger automatic deployment

See [Deployment Guide](docs/deployment.md) for full details.

## Architecture

- **Brain Layer**: LangGraph agents (Elena, Marcus) for reasoning
- **Spine Layer**: Temporal workflows for durable orchestration
- **Memory Layer**: Zep + Graphiti for temporal knowledge graphs
- **Frontend**: React + Vite with voice interaction
- **Backend**: FastAPI with enterprise security

## Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Memory** | Zep (Temporal Knowledge Graph) | Episodic & semantic memory |
| **Orchestration** | Temporal (Durable Workflows) | Long-running, fault-tolerant workflows |
| **Brain** | LangGraph Agents (Python) | Agent reasoning & execution |
| **ETL** | Unstructured.io | Document processing pipeline |
| **Frontend** | React + Vite | 3-column UI with voice interaction |
| **Backend** | FastAPI | REST API & WebSocket server |

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Agent Personas](docs/agents.md)
- [Local Testing Guide](docs/local-testing.md)
- [GitHub Secrets Configuration](docs/github-secrets.md)
- [Deployment Guide](docs/deployment.md)
- [FinOps Strategy](docs/finops.md)
- [Azure PostgreSQL](docs/azure-postgresql.md)

**Full documentation**: [Wiki](https://wiki.engram.work)

## Features

- 🧠 **Context Engineering** - 4-layer enterprise context schema
- 🦴 **Durable Workflows** - Temporal-based orchestration
- 💾 **Temporal Knowledge Graph** - Zep + Graphiti memory
- 🎤 **Voice Interaction** - Azure Speech SDK with avatar
- 🔐 **Enterprise Security** - Entra ID + RBAC
- 💰 **FinOps-First** - Scale-to-zero architecture

## License

MIT
