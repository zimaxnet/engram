# Staging POC Environment Deployment

This directory contains the Infrastructure as Code (IAC) for the **Staging POC** environment.

## Overview

- **Environment**: Staging POC
- **Compute**: Azure Container Apps (Consumption plan, scale-to-zero)
- **Database**: PostgreSQL B1ms (1 vCore, 2GB RAM, 32GB storage)
- **Storage**: Blob Storage (Standard LRS, Hot tier)
- **Estimated Cost**: ~$23/month (idle), ~$50-80/month (light usage)

## Prerequisites

1. Azure subscription with appropriate permissions
2. Azure CLI installed and configured
3. Resource group created: `rg-engram-staging`
4. Key Vault with required secrets:
   - `postgres-password`
   - `registry-username`
   - `registry-password`
   - `zep-api-key`
   - `azure-ai-key`

## Deployment

### Step 1: Create Resource Group

```bash
az group create \
  --name rg-engram-staging \
  --location eastus
```

### Step 2: Deploy Infrastructure

```bash
az deployment group create \
  --resource-group rg-engram-staging \
  --template-file ../../main.bicep \
  --parameters @parameters.json
```

### Step 3: Verify Deployment

```bash
# Check Container Apps
az containerapp list --resource-group rg-engram-staging

# Check PostgreSQL
az postgres flexible-server show \
  --resource-group rg-engram-staging \
  --name engram-staging-db

# Check Storage Account
az storage account show \
  --resource-group rg-engram-staging \
  --name engramstagingstore
```

## Configuration

The staging environment uses:
- **Scale-to-zero**: All container apps scale to 0 replicas when idle
- **Minimal resources**: B1ms PostgreSQL, minimal storage
- **No Private Link**: Public endpoints for cost optimization
- **30-day log retention**: Basic logging

## Cost Optimization

- Scale-to-zero when idle (no compute costs)
- Use B1ms PostgreSQL (cheapest tier)
- Minimal storage allocation
- Basic monitoring (30-day retention)

## Troubleshooting

See the main [infra/README.md](../../README.md) for troubleshooting guidance.

