---
description: Shut down all Azure resources for the night to minimize costs (FinOps)
---

# Azure Nightly Shutdown

This workflow stops all Azure Container Apps and the PostgreSQL database to minimize costs during off-hours.

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Access to the `engram-rg` resource group

## Steps

### 1. Scale Container Apps to Zero

Stop all container apps by setting replicas to 0:

// turbo

```bash
az containerapp update --name staging-env-zep --resource-group engram-rg --min-replicas 0 --max-replicas 0
```

// turbo

```bash
az containerapp update --name staging-env-api --resource-group engram-rg --min-replicas 0 --max-replicas 0
```

// turbo

```bash
az containerapp update --name staging-env-worker --resource-group engram-rg --min-replicas 0 --max-replicas 0
```

// turbo

```bash
az containerapp update --name staging-env-temporal-server --resource-group engram-rg --min-replicas 0 --max-replicas 0
```

// turbo

```bash
az containerapp update --name staging-env-temporal-ui --resource-group engram-rg --min-replicas 0 --max-replicas 0
```

### 2. Stop PostgreSQL Database

After containers are scaled down, stop the database:

```bash
az postgres flexible-server stop --resource-group engram-rg --name staging-env-db
```

### 3. Verify Shutdown

Confirm all resources are stopped:

// turbo

```bash
az containerapp list --resource-group engram-rg --query "[].{name:name, replicas:properties.template.scale}" --output table
```

// turbo

```bash
az postgres flexible-server show --resource-group engram-rg --name staging-env-db --query "{name:name, state:state}" --output table
```

## Expected Result

- All Container Apps should show `minReplicas: 0, maxReplicas: 0`
- PostgreSQL should show `state: Stopped`

## Cost Savings

When stopped:

- **Container Apps**: $0 (scale-to-zero)
- **PostgreSQL B1ms**: ~$0 when stopped (only storage costs ~$0.10/GB/month)
