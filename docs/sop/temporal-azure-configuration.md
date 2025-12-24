# Temporal on Azure Container Apps: Complete Setup Guide

> **Last Updated**: December 24, 2025  
> **Status**: Production-Ready ✅  
> **Maintainer**: Engram Platform Team

## Executive Summary

This document provides the complete, battle-tested configuration for running Temporal durable workflows on Azure Container Apps (ACA). After extensive debugging on December 23-24, 2025, we identified the exact networking requirements for gRPC communication.

## TL;DR - The Working Configuration

```text
Temporal Server:
  - Ingress Type: EXTERNAL (not internal!)
  - Transport: HTTP/2
  - Target Port: 7233
  - FQDN: staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io

Worker/API Connection:
  - Endpoint: {server-fqdn}:443 (NOT :7233!)
  - TLS: Enabled (required)
  - Protocol: gRPC over HTTPS
```

---

## Step-by-Step Setup Guide

### Step 1: Deploy Temporal Server with Correct Ingress

The Temporal Server must use **external** ingress with **HTTP/2** transport.

```bicep
// infra/modules/temporal-aca.bicep
resource temporalServer 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${appName}-server'
  properties: {
    configuration: {
      ingress: {
        // CRITICAL: Must be external for gRPC to work!
        external: true
        targetPort: 7233
        // REQUIRED: HTTP/2 transport for gRPC protocol
        transport: 'http2'
        allowInsecure: false
      }
    }
    template: {
      containers: [{
        name: 'temporal-server'
        image: 'temporalio/auto-setup:latest'
        env: [
          { name: 'DB', value: 'postgres12' }
          { name: 'POSTGRES_USER', value: 'cogadmin' }
          { name: 'POSTGRES_PWD', secretRef: 'postgres-password' }
          { name: 'POSTGRES_SEEDS', value: '<postgres-fqdn>' }
          { name: 'POSTGRES_DB', value: '<database-name>' }
          // IMPORTANT: Set to false to auto-create "default" namespace
          { name: 'SKIP_DEFAULT_NAMESPACE_CREATION', value: 'false' }
          { name: 'SQL_TLS', value: 'true' }
          { name: 'SQL_TLS_ENABLED', value: 'true' }
          { name: 'POSTGRES_TLS_ENABLED', value: 'true' }
          { name: 'POSTGRES_TLS_DISABLE_HOST_VERIFICATION', value: 'true' }
        ]
      }]
    }
  }
}
```

**If already deployed with wrong config, fix via CLI:**

```bash
# Make ingress external
az containerapp ingress update \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --type external

# Set HTTP/2 transport
az containerapp ingress update \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --transport http2

# Enable namespace creation
az containerapp update \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --set-env-vars "SKIP_DEFAULT_NAMESPACE_CREATION=false"
```

### Step 2: Get the Temporal Server FQDN

```bash
az containerapp show \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv

# Example output:
# staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io
```

⚠️ **IMPORTANT**: The FQDN should NOT contain `.internal.` - if it does, your ingress is still set to internal.

### Step 3: Configure Worker with Correct TEMPORAL_HOST

The worker must connect to **port 443** (not 7233) because Azure ingress routes through HTTPS.

```bash
# Set the correct TEMPORAL_HOST format
az containerapp update \
  --name staging-env-worker \
  --resource-group engram-rg \
  --set-env-vars \
    "TEMPORAL_HOST=staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io:443" \
    "TEMPORAL_NAMESPACE=default" \
    "TEMPORAL_TASK_QUEUE=engram-agents"
```

### Step 4: Configure API with Same TEMPORAL_HOST

```bash
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars \
    "TEMPORAL_HOST=staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io:443" \
    "TEMPORAL_NAMESPACE=default" \
    "TEMPORAL_TASK_QUEUE=engram-agents"
```

### Step 5: Update Python SDK to Use TLS

The Temporal Python SDK must enable TLS when connecting through Azure ingress.

```python
# backend/workflows/worker.py and backend/workflows/client.py

async def create_temporal_client() -> Client:
    """Create a Temporal client with Azure Container Apps support"""
    settings = get_settings()

    host_parts = settings.temporal_host.split(":")
    host = host_parts[0]
    port = int(host_parts[1]) if len(host_parts) > 1 else 7233

    logger.info(f"Connecting to Temporal at {host}:{port}")

    # Azure Container Apps ingress uses TLS on port 443
    use_tls = port == 443 or ".azurecontainerapps.io" in host
    
    if use_tls:
        logger.info("Using TLS for Azure Container Apps connection")
        client = await Client.connect(
            f"{host}:{port}",
            namespace=settings.temporal_namespace,
            tls=True,  # REQUIRED for Azure Container Apps
        )
    else:
        client = await Client.connect(
            f"{host}:{port}",
            namespace=settings.temporal_namespace,
        )

    logger.info(f"Connected to Temporal namespace: {settings.temporal_namespace}")
    return client
```

### Step 6: Add Required Secrets to Worker

The worker needs the Anthropic API key for story generation:

```bash
# Copy secret from API to worker
ANTHROPIC_KEY=$(az containerapp secret show \
  --name staging-env-api \
  --resource-group engram-rg \
  --secret-name anthropic-api-key \
  --query "value" --output tsv)

az containerapp secret set \
  --name staging-env-worker \
  --resource-group engram-rg \
  --secrets "anthropic-api-key=$ANTHROPIC_KEY"

az containerapp update \
  --name staging-env-worker \
  --resource-group engram-rg \
  --set-env-vars "ANTHROPIC_API_KEY=secretref:anthropic-api-key"
```

### Step 7: Verify Connection

**Local Python Test:**

```python
import asyncio
from temporalio.client import Client

async def test():
    client = await Client.connect(
        'staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io:443',
        namespace='default',
        tls=True,
    )
    print('SUCCESS! Connected to Temporal!')

asyncio.run(test())
```

**Check Worker Logs:**

```bash
az containerapp logs show \
  --name staging-env-worker \
  --resource-group engram-rg \
  --type console \
  --tail 20 | grep -i "temporal\|connected\|started"
```

**Expected output:**

```
Connecting to Temporal at ...azurecontainerapps.io:443
Using TLS for Azure Container Apps connection
Connected to Temporal namespace: default
Starting worker on task queue: engram-agents
Worker started successfully
```

### Step 8: Test Story Workflow

```bash
curl -X POST https://engram.work/api/v1/story/create \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test Story", "include_diagram": false}'
```

---

## Troubleshooting Guide

### Error: Connection Timeout to :7233

**Symptom**: `dial tcp 100.100.x.x:7233: i/o timeout`

**Cause**: Connecting to wrong port (7233 instead of 443)

**Fix**: Update TEMPORAL_HOST to use port 443:

```bash
az containerapp update --name staging-env-worker --resource-group engram-rg \
  --set-env-vars "TEMPORAL_HOST=<fqdn>:443"
```

### Error: ConnectionReset / BrokenPipe

**Symptom**: `transport error: hyper::Error(Io, BrokenPipe)`

**Cause**: TLS not enabled in Python SDK

**Fix**: Enable `tls=True` in Client.connect()

### Error: Namespace Not Found

**Symptom**: `Namespace default is not found`

**Cause**: Temporal Server has SKIP_DEFAULT_NAMESPACE_CREATION=true

**Fix**:

```bash
az containerapp update --name staging-env-temporal-server \
  --resource-group engram-rg \
  --set-env-vars "SKIP_DEFAULT_NAMESPACE_CREATION=false"
```

### Error: Anthropic API Key Not Configured

**Symptom**: `Anthropic API key not configured. Cannot invoke Claude.`

**Cause**: Worker missing ANTHROPIC_API_KEY secret

**Fix**: Add the secret (see Step 6 above)

---

## Configuration Summary

| Component | Setting | Value |
|-----------|---------|-------|
| Temporal Server Ingress | `external` | `true` |
| Temporal Server Transport | `transport` | `http2` |
| Temporal Server Port | `targetPort` | `7233` |
| Worker/API TEMPORAL_HOST | Port | `443` (not 7233!) |
| Python SDK | `tls` | `True` |
| Namespace Creation | `SKIP_DEFAULT_NAMESPACE_CREATION` | `false` |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure Container Apps Environment                         │
│                                                                              │
│  ┌──────────────────┐     gRPC/TLS      ┌──────────────────────────────────┐│
│  │   Engram API     │─────────────────▶ │                                  ││
│  │   (Port 8080)    │     port 443      │      Azure Load Balancer         ││
│  └──────────────────┘                   │         (Ingress)                ││
│                                         │                                  ││
│  ┌──────────────────┐     gRPC/TLS      │      TLS Termination + HTTP/2    ││
│  │  Engram Worker   │─────────────────▶ │                                  ││
│  │  (Temporal SDK)  │     port 443      └──────────────────────────────────┘│
│  └──────────────────┘                              │                        │
│                                                    │ HTTP/2                 │
│                                                    ▼                        │
│                                    ┌──────────────────────┐                 │
│                                    │   Temporal Server    │                 │
│                                    │   (Port 7233)        │                 │
│                                    │   temporalio/auto-   │                 │
│                                    │   setup:latest       │                 │
│                                    └──────────────────────┘                 │
│                                                    │                        │
└────────────────────────────────────────────────────│────────────────────────┘
                                                     │ PostgreSQL
                                                     ▼
                                      ┌──────────────────────┐
                                      │  Azure PostgreSQL    │
                                      │  (Temporal DB)       │
                                      └──────────────────────┘
```

---

## Key Discoveries (December 2025)

1. **Internal ingress does NOT work for gRPC** - Azure Container Apps internal routing doesn't properly handle gRPC traffic

2. **Port 443, not 7233** - Azure ingress does TLS termination on port 443 and forwards to the container's targetPort internally

3. **TLS is mandatory** - Even though Azure handles TLS termination, the Python SDK must still use TLS to communicate with the ingress

4. **Namespace must be created** - The `temporalio/auto-setup` image has `SKIP_DEFAULT_NAMESPACE_CREATION=true` by default

---

## Related Documentation

- [Temporal Worker Postmortem](./temporal-worker-postmortem.md)
- [Azure Container Apps gRPC Support](https://learn.microsoft.com/en-us/azure/container-apps/grpc)
- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-24 | Complete step-by-step guide added |
| 2025-12-24 | Successfully tested story workflow execution |
| 2025-12-23 | Initial debugging and discovery of configuration requirements |
