# Engram

<!-- Deployment trigger: Updated UI to show Model Router --> - Context Engineering Platform

> **Cognition-as-a-Service for the Enterprise**

Engram is an enterprise-grade AI platform that solves the **Memory Wall Problem** in Large Language Models through innovative context engineering. Built on the **Brain + Spine** architecture pattern, Engram provides durable, scalable, and cost-effective AI agent orchestration.

## Quick Start

### Local Development

1. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env and add your Azure AI Foundry endpoint + key (AZURE_AI_ENDPOINT, AZURE_AI_KEY, AZURE_AI_DEPLOYMENT)
   # Ensure AUTH_REQUIRED=false is set in .env for local development to bypass authentication
   ```

2. **Start services**:

   ```bash
   docker-compose up -d postgres zep temporal temporal-ui
   ```

3. **Install dependencies**:

   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

4. **Start Development Server**:

   ```bash
   # From root directory
   npm run dev
   ```

   *Alternatively, run services individually:*
   - **Backend**: `npm run start:backend` (Runs on port 8082)
   - **Frontend**: `npm run start:frontend` (Runs on port 5173)

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
| **Brain** | LangGraph Agents (python) | Agent reasoning & execution |
| **ETL** | Unstructured.io | Document processing (PDF, DOCX) & Ingestion |
| **Frontend** | React + Vite | Premium UI with Sidebar Concept Explainer |
| **Backend** | FastAPI | REST API & WebSocket server |

## System Capabilities

### 1. Document Ingestion (ETL)

Upload documents (PDF, DOCX, TXT) to the Knowledge Graph.

- **Endpoint**: `POST /api/v1/etl/ingest`
- **Process**: Partitioning -> Chunking -> Embedding -> Zep Memory

### 2. Episodic Memory

The agent "remembers" past conversations and facts.

- **View Transcripts**: See full history of past episodes.
- **Search**: Hybrid search across semantic facts and episodic history.

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
- 🚦 **System Navigator** - Comprehensive admin & memory explorer UI
- 🔑 **Foundry Key Auth** - Azure AI Services via key-only configuration
- 🔐 **Enterprise Security** - Entra ID + RBAC
- 💰 **FinOps-First** - Scale-to-zero architecture

## 🤖 Emerging Context for AI Agents

We provide specific context files to help AI IDEs (Cursor, VS Code) and Agents understand the system's capabilities immediately.

See [Engram Capabilities](docs/ide-context/engram-capabilities.md) for available tools:
- **Sage Storyteller**: Generate narratives & visuals (`simulate_sage_story.py`)
- **Tri-Search**: Keyword, Vector, Graph memory integration
- **Data Connectors**: Ingest Wiki, Tickets, and Code

## License

MIT
