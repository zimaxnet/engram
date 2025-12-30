# Engram Enterprise POC Guide

This guide provides a comprehensive overview of the Engram Enterprise Proof of Concept (POC) environment, designed for validating the system's architecture, security, and capabilities within your Azure subscription.

## 1. System Architecture

The Engram platform is deployed as a set of cloud-native microservices on Azure, leveraging specific enterprise-grade components for security and scalability.

```mermaid
graph TD
    User([User]) -->|HTTPS| FrontDoor[Azure Front Door / CDN]
    FrontDoor -->|Static Content| SWA[Static Web App (Frontend)]
    FrontDoor -->|API Requests| ACAEnv[Azure Container Apps Environment]
    
    subgraph ACAEnv
        API[Backend API]
        Worker[Background Worker]
        Zep[Zep Memory Service]
        Temporal[Temporal Orchestrator]
    end
    
    SWA -->|Auth (Entra ID)| Entra[Microsoft Entra ID]
    API -->|Validate Token| Entra
    
    API -->|Persist| PG[(Postgres Flexible Server)]
    API -->|Recall| Zep
    API -->|Orchestrate| Temporal
    
    Zep -->|Vector Store| PG
    Temporal -->|State Store| PG
    
    API -->|Docs/Artifacts| Blob[Storage Account]
    API -->|AI Models| AI[Azure AI Foundry]
```

### Components

| Component | Service Type | Role |
|-----------|--------------|------|
| **Frontend** | Azure Static Web Apps | Hosts the React/Vite SPA. Handles user authentication via MSAL (Entra External ID). |
| **Backend API** | Azure Container App | FastAPI service. Handles business logic, agent orchestration, and API endpoints. |
| **Memory (Zep)** | Azure Container App | Long-term memory and knowledge graph service. Stores embeddings in Postgres (pgvector). |
| **Orchestrator** | Azure Container App | Temporal server. Manages durable workflows (long-running agent tasks). |
| **Database** | Postgres Flexible Server | Unified data store. Databases: `engram` (app), `zep` (memory), `temporal` (workflows). |
| **Storage** | Azure Storage Account | Blob storage for raw documents; File share for persistent configuration. |
| **AI Gateway** | Azure AI Foundry | Central access point for LLMs (GPT-4o, Claude, etc.) and embeddings. |

## 2. Startup Sequence

When the environment is deployed or restarted, the services initialize in a specific order to ensure dependency resolution.

1. **Infrastructure Initialization**
    * **PostgreSQL** starts and accepts connections.
    * **Key Vault** becomes accessible to Managed Identities.

2. **Core Services (Recall & Orchestration)**
    * **Zep** container starts. It runs migrations on the `zep` database and initializes the vector search indexes.
    * **Temporal** container starts. It connects to the `temporal` database and ensures the history and matching services are ready.

3. **Application Layer**
    * **Backend API** container starts (waits for Postgres and Temporal).
    * **Migration**: Validates schema versions for the `engram` database.
    * **Auth**: Loads `AUTH_REQUIRED` setting and connects to Entra ID for JWKS (for token validation).
    * **Connection**: Establishes gRPC connection to Temporal and HTTP connection to Zep.

4. **Presentation Layer**
    * **Static Web App** serves the UI.
    * User logs in via Entra ID (pop-up/redirect flow).
    * Frontend acquires an Access Token (`Bearer ...`) scoped to the specific user and tenant.

## 3. Deployment Validation

To verify the deployment is successful and "stable" for enterprise use:

### A. Infrastructure Health

Check that all Container Apps in the resource group show a status of **Running** (or Succeeded).

* `engram-api`
* `engram-worker`
* `engram-zep`
* `engram-temporal`

### B. Authentication Check

1. Navigate to `https://<your-env>.engram.work` (e.g., `https://staging.engram.work`).
2. Click **Login**. You should be redirected to your Entra ID tenant login page.
3. After successful login, the "User Menu" (top right) should display your user profile.

### C. Functional Smoke Test

1. **Chat**: Send a message "Hello, who are you?". The agent (Elena) should reply, citing its system prompt (context).
2. **Memory**: Tell the agent "My favorite color is blue." Then ask "What is my favorite color?". It should retrieve this from Zep memory.
3. **Artifacts**: Ask "Create a story about a cloud deployment." The system should trigger a Temporal workflow to generate a markdown artifact.

## 4. Troubleshooting

| Symptom | Probable Cause | Fix |
|---------|----------------|-----|
| **401 Unauthorized** | Missing Entra ID params in deployment or GitHub secrets. | Run `scripts/setup-github-secrets.sh` and redeploy. |
| **"Stories missing token"** | Frontend built without Client ID. | Re-run "Deploy" GitHub Action after setting secrets. |
| **Chat Hanging/spin** | Temporal or Zep service down. | Check Container App logs for `engram-temporal` or `engram-zep`. |
| **Voice Latency** | Cold start of VoiceLive service. | Allow 10-15s for first connection; subsequent should be sub-second. |

---
**POC Contact:** <support@engram.work>
