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

> [!WARNING]
> **Manual Container Start May Be Required**
>
> After running the `az containerapp update` commands below, containers may show `Running: Stopped` with 0 replicas despite `minReplicas: 1`. If this happens:
>
> 1. Go to **Azure Portal** → **Container Apps**
> 2. Select each container app
> 3. Click **Start** manually
>
> This is a known Azure behavior when containers have been scaled to zero.

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

### 9. Verify Public Access (Critical)

// turbo

This confirms the API is reachable and authentication is correctly configured (bypassed).

```bash
curl -s https://api.engram.work/health | jq .
```

Expected output: `{"status":"healthy"...}`.
If you get `401 Unauthorized`, Platform Auth may have been re-enabled. Disable it with:
`az containerapp auth update --name staging-env-api --resource-group engram-rg --enabled false`

### 10. E2E Memory Verification (Full Pipeline Test)

// turbo

Enriches a test episode and verifies it appears in episodes, search, and knowledge graph.

```bash
./scripts/verify-memory-e2e.sh
```

Expected output: All 4 checks should pass ✅

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
3. Restart Zep: `az containerapp revision restart --name staging-env-zep --resource-group engram-rg --revision $(az containerapp revision list --name staging-env-zep --resource-group engram-rg --query "[0].name\" -o tsv)`

## Post-Startup: Document Findings

> [!TIP]
> Always document startup findings and enrich memory so learnings are searchable.

### 11. Document Startup Report (Standard Practice)

After verification, document any challenges or findings:

1. **Note key findings** (CORS issues, auth reverts, stale revisions, etc.)
2. **Enrich memory** via the API:

```bash
curl -X POST "https://api.engram.work/api/v1/memory/enrich" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Startup Report [DATE]: [KEY FINDINGS]",
    "session_id": "startup-episode-[YYYYMMDD]",
    "speaker": "assistant",
    "agent_id": "antigravity",
    "channel": "automation"
  }'
```

1. **Verify in Episodes UI** at <https://engram.work/memory/episodes>
