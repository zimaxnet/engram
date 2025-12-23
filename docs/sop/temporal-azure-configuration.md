# Temporal on Azure Container Apps: Configuration Guide

> **Last Updated**: December 23, 2025  
> **Status**: Production-Ready ✅  
> **Maintainer**: Engram Platform Team

## Overview

This document provides the definitive configuration for running Temporal durable workflows on Azure Container Apps (ACA). After extensive debugging, we identified the exact networking requirements for gRPC communication between the Temporal Server and Workers.

## TL;DR - The Working Configuration

```
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

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Azure Container Apps Environment                         │
│  ┌──────────────────┐                      ┌──────────────────┐            │
│  │   Temporal UI    │                      │   Engram API     │            │
│  │   (Port 8080)    │                      │   (Port 8080)    │            │
│  └────────┬─────────┘                      └────────┬─────────┘            │
│           │                                         │                       │
│           │  HTTP                                   │  gRPC/TLS             │
│           ▼                                         ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Azure Load Balancer / Ingress                     │  │
│  │                         (TLS Termination)                             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    │ HTTP/2                                 │
│                                    ▼                                        │
│                      ┌──────────────────────┐                              │
│                      │   Temporal Server    │                              │
│                      │   (Port 7233)        │                              │
│                      │   HTTP/2 Transport   │                              │
│                      └──────────────────────┘                              │
│                                    ▲                                        │
│                                    │ gRPC/TLS (port 443)                    │
│  ┌──────────────────┐             │                                        │
│  │  Engram Worker   │─────────────┘                                        │
│  │  (Temporal SDK)  │                                                      │
│  └──────────────────┘                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                      ┌──────────────────────┐
                      │  Azure PostgreSQL    │
                      │  (Temporal DB)       │
                      └──────────────────────┘
```

---

## Key Discoveries

### 1. Internal Ingress Does NOT Work for gRPC

**Problem**: Azure Container Apps internal ingress (`.internal.` FQDNs) does not reliably route gRPC traffic, even with HTTP/2 transport configured.

**Symptoms**:

- Connection timeouts to port 7233
- `dial tcp 100.100.x.x:7233: i/o timeout`
- Worker containers restart repeatedly

**Solution**: Use **external ingress** for the Temporal Server.

### 2. Port 443 Instead of 7233

**Problem**: Azure Container Apps ingress routes through port 443 (HTTPS), not the container's target port directly.

**Symptoms**:

- Direct connection to `:7233` times out
- Connection to `:443` reaches the container

**Solution**: Connect to port **443**, not 7233. The ingress handles port translation internally.

### 3. TLS Must Be Explicitly Enabled

**Problem**: The Temporal SDK defaults to plaintext gRPC. Azure ingress requires TLS.

**Symptoms**:

- `ConnectionReset` or `BrokenPipe` errors
- `transport error` in connection logs

**Solution**: Enable TLS in the Temporal client:

```python
client = await Client.connect(
    f"{host}:443",
    namespace="default",
    tls=True,  # REQUIRED for Azure Container Apps
)
```

---

## Temporal Server Configuration

### Bicep/ARM Configuration

```bicep
resource temporalServer 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'staging-env-temporal-server'
  properties: {
    configuration: {
      ingress: {
        external: true          // EXTERNAL, not internal!
        targetPort: 7233
        transport: 'http2'      // Required for gRPC
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'temporal-server'
          image: 'temporalio/auto-setup:latest'
          env: [
            { name: 'DB', value: 'postgres12' }
            { name: 'POSTGRES_USER', value: 'cogadmin' }
            { name: 'POSTGRES_PWD', secretRef: 'postgres-password' }
            { name: 'POSTGRES_SEEDS', value: '<postgres-fqdn>' }
            // ... other env vars
          ]
        }
      ]
    }
  }
}
```

### Azure CLI Commands

```bash
# Set transport to HTTP/2 (required for gRPC)
az containerapp ingress update \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --transport http2

# Make ingress external (required for reliable gRPC)
az containerapp ingress update \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --type external

# Get the FQDN
az containerapp show \
  --name staging-env-temporal-server \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv
```

---

## Worker/API Client Configuration

### Environment Variables

```bash
# For Worker and API containers
TEMPORAL_HOST=staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io:443
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=engram-agents
```

### Python Code with TLS Support

```python
# backend/workflows/worker.py

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
            tls=True,  # Enable TLS
        )
    else:
        client = await Client.connect(
            f"{host}:{port}",
            namespace=settings.temporal_namespace,
        )

    logger.info(f"Connected to Temporal namespace: {settings.temporal_namespace}")
    return client
```

---

## Verification

### Test Connection Locally

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

### Verify Worker Connection

Check worker logs for successful connection:

```bash
az containerapp logs show \
  --name staging-env-worker \
  --resource-group engram-rg \
  --type console \
  --tail 20 | grep -i "temporal\|connected\|started"
```

**Expected output**:

```
Connecting to Temporal at staging-env-temporal-server...azurecontainerapps.io:443
Using TLS for Azure Container Apps connection
Connected to Temporal namespace: default
Starting worker on task queue: engram-agents
Worker started successfully
```

### Verify via HTTP

```bash
# Should return 415 (Unsupported Media Type) - confirms server is responding
curl -s -o /dev/null -w "%{http_code}" \
  https://staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io/
```

---

## Troubleshooting

### Error: Connection Timeout

**Symptom**: `dial tcp ... i/o timeout`

**Cause**: Temporal Server ingress is internal or using wrong port

**Fix**:

1. Set ingress to `external`
2. Use port `443` in TEMPORAL_HOST

### Error: ConnectionReset / BrokenPipe

**Symptom**: `transport error: hyper::Error(Io, BrokenPipe)`

**Cause**: TLS not enabled in client

**Fix**: Set `tls=True` in Client.connect()

### Error: operation was canceled

**Symptom**: `connection closed` or `operation was canceled`

**Cause**: Old container image without TLS code

**Fix**: Deploy new image with TLS support in create_temporal_client()

### Worker Keeps Restarting

**Symptom**: Logs show "Connecting to Temporal..." repeatedly

**Cause**: Connection failing, container restarting

**Fix**: Check all of the above, ensure CI deployed new image

---

## Common Mistakes to Avoid

| ❌ Don't | ✅ Do |
|---------|-------|
| Use internal ingress (`.internal.`) | Use external ingress |
| Connect to port 7233 | Connect to port 443 |
| Use plaintext gRPC | Enable `tls=True` |
| Use simplified hostname (`app-name:7233`) | Use full FQDN with port 443 |
| Expect immediate changes | Wait for new container revision |

---

## Related Documentation

- [Temporal Worker Postmortem](./temporal-worker-postmortem.md) - Details on the WORKER_MODE Dockerfile fix
- [Azure Container Apps gRPC Support](https://learn.microsoft.com/en-us/azure/container-apps/grpc)
- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [Temporal Self-Hosted Guide](https://docs.temporal.io/self-hosted-guide)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-23 | Initial documentation with working configuration |
| 2025-12-23 | Added TLS requirement discovery |
| 2025-12-23 | Confirmed external ingress requirement |
