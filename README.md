# Cognitive Enterprise Architecture (PoC)

This repository contains the "Memory Wall" solution Proof of Concept, deployed as a set of microservices on Azure.

## Components
- **Memory**: Zep (Temporal Knowledge Graph).
- **Orchestration**: Temporal (Durable Workflows).
- **Brain**: LangGraph Agent (Python).
- **ETL**: Unstructured.io pipeline.

## Getting Started

### Local Development
Run the entire stack locally with Docker Compose:
```bash
docker-compose up --build
```

### Azure Deployment
The infrastructure is defined in Bicep. See `infra/README.md` for details.
**Strategy**: Azure Container Apps (Serverless) + Postgres Flexible Server.

### Documentation
Full architecture and FinOps details are available in the [Wiki](https://wiki.engram.work).
