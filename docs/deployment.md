---
layout: default
title: Deployment Guide
---

# [Home](/) › Deployment Guide

# Deployment Guide

This guide covers deploying the Engram platform to Azure and local development setup.

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Azure CLI | 2.50+ | Azure resource management |
| Docker | 24+ | Container builds |
| Node.js | 20+ | Frontend build |
| Python | 3.11+ | Backend development |
| Bicep CLI | Latest | Infrastructure as code |

### Azure Resources

Ensure you have:
- Azure subscription with Owner or Contributor access
- Resource provider registrations for:
  - Microsoft.App (Container Apps)
  - Microsoft.KeyVault
  - Microsoft.DBforPostgreSQL
  - Microsoft.Storage
  - Microsoft.CognitiveServices

---

## Local Development

### Quick Start

```bash
# Clone the repository
git clone https://github.com/zimaxnet/engram.git
cd engram

# Create environment file
cp .env.example .env
# Edit .env with your Azure AI Foundry credentials

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the platform
open http://localhost:5173
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React UI |
| API | http://localhost:8082 | FastAPI backend |
| Temporal UI | http://localhost:8080 | Workflow monitoring |
| Zep | http://localhost:8000 | Memory service |
| PostgreSQL | localhost:5432 | Database |

### Environment Variables

```bash
# .env file
ENVIRONMENT=development
DEBUG=true

# Azure AI Foundry (required for agent functionality)
AZURE_AI_ENDPOINT=https://your-endpoint.services.ai.azure.com/
AZURE_AI_KEY=your-key-here
AZURE_AI_DEPLOYMENT=gpt-4o-mini

# Database (defaults work for docker-compose)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=engram
```

---

## Azure Deployment

### 1. Infrastructure Setup

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "Your Subscription Name"

# Create resource group
az group create \
  --name engram-rg \
  --location eastus

# Deploy infrastructure
az deployment group create \
  --resource-group engram-rg \
  --template-file infra/main.bicep \
  --parameters environment=production
```

### 2. Key Vault Secrets

```bash
# Get Key Vault name from deployment output
KV_NAME=$(az deployment group show \
  --resource-group engram-rg \
  --name main \
  --query properties.outputs.keyVaultName.value -o tsv)

# Set required secrets
az keyvault secret set --vault-name $KV_NAME \
  --name "azure-ai-key" --value "your-foundry-key"

az keyvault secret set --vault-name $KV_NAME \
  --name "azure-client-id" --value "your-entra-client-id"

az keyvault secret set --vault-name $KV_NAME \
  --name "azure-client-secret" --value "your-entra-client-secret"

az keyvault secret set --vault-name $KV_NAME \
  --name "azure-tenant-id" --value "your-tenant-id"
```

### 3. Container Deployment

```bash
# Build and push images
docker build -t ghcr.io/zimaxnet/engram/backend:latest ./backend
docker build -t ghcr.io/zimaxnet/engram/worker:latest -f ./backend/workflows/Dockerfile ./backend

docker push ghcr.io/zimaxnet/engram/backend:latest
docker push ghcr.io/zimaxnet/engram/worker:latest

# Deploy to Container Apps (via GitHub Actions or manual)
az containerapp update \
  --name engram-api \
  --resource-group engram-rg \
  --image ghcr.io/zimaxnet/engram/backend:latest
```

### 4. Frontend Deployment

```bash
# Build frontend
cd frontend
npm ci
npm run build

# Deploy to Static Web Apps
az staticwebapp create \
  --name engram-frontend \
  --resource-group engram-rg \
  --source ./dist \
  --location eastus
```

---

## CI/CD Pipeline

The repository includes GitHub Actions workflows:

### CI Pipeline (`.github/workflows/ci.yml`)

Triggers: Push to `main`/`develop`, Pull Requests

Steps:
1. Backend tests with PostgreSQL service
2. Frontend linting and build
3. Security scanning with Trivy
4. Docker image builds

### Deploy Pipeline (`.github/workflows/deploy.yml`)

Triggers: CI success on `main`, Manual dispatch

Steps:
1. Deploy infrastructure (Bicep)
2. Deploy backend to Container Apps
3. Deploy worker to Container Apps
4. Deploy frontend to Static Web Apps
5. Health checks
6. Notifications

### Required Secrets

Set these in GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON |
| `AZURE_KEY_VAULT_URL` | Key Vault URL |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | SWA deployment token |
| `API_URL` | Production API URL |
| `WS_URL` | Production WebSocket URL |
| `SLACK_WEBHOOK_URL` | (Optional) Notifications |

---

## Entra ID Setup

### App Registration

1. Go to Azure Portal > Microsoft Entra ID > App registrations
2. Click "New registration"
3. Configure:
   - Name: `Engram Platform`
   - Supported account types: Single tenant (or as needed)
   - Redirect URI: `https://your-frontend.azurestaticapps.net/callback`

4. Note the Application (client) ID and Directory (tenant) ID

5. Create client secret:
   - Certificates & secrets > New client secret
   - Copy the secret value immediately

6. Configure API permissions:
   - Microsoft Graph > User.Read
   - Add custom scopes as needed

7. Update app manifest with roles:
```json
"appRoles": [
  {
    "allowedMemberTypes": ["User"],
    "displayName": "Admin",
    "id": "generate-uuid",
    "value": "Admin"
  },
  {
    "allowedMemberTypes": ["User"],
    "displayName": "Analyst",
    "id": "generate-uuid",
    "value": "Analyst"
  }
]
```

---

## Health Checks

### API Health

```bash
curl https://your-api.azurecontainerapps.io/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "healthy",
    "temporal": "healthy",
    "zep": "healthy"
  }
}
```

### Temporal Health

Access Temporal UI at your deployed URL to verify:
- Workers are running
- Task queues have active pollers
- No failed workflows

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Check Entra ID config |
| 500 on agent calls | Missing AZURE_AI_KEY | Verify Key Vault secrets |
| Workflows not running | Worker not started | Check worker logs, task queue |
| Memory errors | Zep connection failed | Verify Zep URL and health |

### Viewing Logs

```bash
# Container Apps logs
az containerapp logs show \
  --name engram-api \
  --resource-group engram-rg \
  --follow

# Worker logs
az containerapp logs show \
  --name engram-worker \
  --resource-group engram-rg \
  --follow
```

### Debug Mode

Set `DEBUG=true` in environment to enable:
- Detailed error messages
- API documentation at `/docs`
- Verbose logging

