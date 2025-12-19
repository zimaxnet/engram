---
description: Start all Azure resources in the morning (FinOps)
---

# Azure Morning Startup

This workflow starts all Azure resources in the correct order. **PostgreSQL must be started first** before containers, as they depend on the database.

## Prerequisites

- Azure CLI installed and logged in (`az login`)
- Access to the `engram-rg` resource group

## Steps

### 1. Start PostgreSQL Database (FIRST!)

The database must be running before any containers start:

```bash
az postgres flexible-server start --resource-group engram-rg --name staging-env-db
```

> **Note**: This takes 2-3 minutes. Wait for completion before proceeding.

### 2. Verify Database is Running

// turbo

```bash
az postgres flexible-server show --resource-group engram-rg --name staging-env-db --query "{name:name, state:state}" --output table
```

Expected: `state: Ready`

### 3. Start Temporal Server (Core Dependency)

Temporal must be running before API/Worker:

// turbo

```bash
az containerapp update --name staging-env-temporal-server --resource-group engram-rg --min-replicas 1 --max-replicas 1
```

### 4. Start Zep Memory Service

// turbo

```bash
az containerapp update --name staging-env-zep --resource-group engram-rg --min-replicas 1 --max-replicas 2
```

### 5. Start API and Worker

Once Temporal and Zep are ready:

// turbo

```bash
az containerapp update --name staging-env-api --resource-group engram-rg --min-replicas 1 --max-replicas 3
```

// turbo

```bash
az containerapp update --name staging-env-worker --resource-group engram-rg --min-replicas 1 --max-replicas 2
```

### 6. Start Temporal UI (Optional)

// turbo

```bash
az containerapp update --name staging-env-temporal-ui --resource-group engram-rg --min-replicas 1 --max-replicas 1
```

### 7. Verify All Services Running

// turbo

```bash
az containerapp list --resource-group engram-rg --query "[].{name:name, running:properties.runningStatus}" --output table
```

### 8. Health Check

// turbo

```bash
az containerapp logs show --name staging-env-zep --resource-group engram-rg --type console --tail 5
```

## Startup Order Summary

```
PostgreSQL (2-3 min)
    └── Temporal Server
            └── Zep
                 └── API + Worker
                        └── Temporal UI
```

## Troubleshooting

If Zep fails to start with connection errors:

1. Verify PostgreSQL is fully `Ready` (not just starting)
2. Check `max_connections` is still set to 100
3. Restart Zep: `az containerapp revision restart --name staging-env-zep --resource-group engram-rg --revision $(az containerapp revision list --name staging-env-zep --resource-group engram-rg --query "[0].name" -o tsv)`
