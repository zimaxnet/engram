# Temporal Integration Journey - December 23-24, 2025

## Session Overview

This document captures the complete debugging journey to get Temporal durable workflows functioning on Azure Container Apps for the Engram Context Engine.

## Problem Statement

The Temporal worker could not connect to the Temporal Server running on Azure Container Apps. Initial symptoms:

- Connection timeout to port 7233
- Worker continuously restarting
- Story creation via API returning "Backend call failure"

## Root Causes Discovered

### 1. Worker Running Wrong Process

The `staging-env-worker` container was running Uvicorn (the API server) instead of the Temporal worker process.

**Solution**: Modified `backend/Dockerfile` to support `WORKER_MODE` build argument:

```dockerfile
ARG WORKER_MODE=false
ENV WORKER_MODE=${WORKER_MODE}
# Entrypoint script checks WORKER_MODE and runs appropriate process
```

### 2. Internal Ingress Doesn't Support gRPC

Azure Container Apps internal ingress (`.internal.` FQDNs) does not properly route gRPC traffic between containers.

**Solution**: Changed Temporal Server ingress from `internal` to `external`:

```bash
az containerapp ingress update --name staging-env-temporal-server \
  --resource-group engram-rg --type external
```

### 3. Missing HTTP/2 Transport

gRPC requires HTTP/2 protocol, but Azure Container Apps defaults to HTTP/1.1.

**Solution**: Set transport to `http2`:

```bash
az containerapp ingress update --name staging-env-temporal-server \
  --resource-group engram-rg --transport http2
```

### 4. Wrong Port (7233 vs 443)

Azure ingress routes through port 443 (HTTPS), not the container's internal port.

**Solution**: Connect to port 443, not 7233:

```bash
TEMPORAL_HOST=staging-env-temporal-server...azurecontainerapps.io:443
```

### 5. TLS Not Enabled in Python SDK

The Temporal Python SDK defaults to plaintext gRPC, but Azure ingress requires TLS.

**Solution**: Added conditional TLS logic to Python client:

```python
if port == 443 or ".azurecontainerapps.io" in host:
    client = await Client.connect(f"{host}:{port}", namespace=..., tls=True)
```

### 6. Namespace Not Created

The Temporal Server was configured to skip default namespace creation.

**Solution**: Set environment variable:

```bash
SKIP_DEFAULT_NAMESPACE_CREATION=false
```

### 7. Missing Anthropic API Key

The worker container was missing the Anthropic API key secret for Claude.

**Solution**: Added secret and environment variable mapping:

```bash
az containerapp secret set --name staging-env-worker \
  --secrets "anthropic-api-key=$KEY"
az containerapp update --name staging-env-worker \
  --set-env-vars "ANTHROPIC_API_KEY=secretref:anthropic-api-key"
```

## Successful Outcome

After applying all fixes, the story generation workflow executed successfully via Temporal:

```
Connecting to Temporal at ...azurecontainerapps.io:443
Using TLS for Azure Container Apps connection
Connected to Temporal namespace: default
Worker started successfully
Starting story workflow: story-ad164660033c
Step 1: Generating story with Claude...
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
Story generated: 14335 chars
Artifacts saved: docs/stories/20251224-020303-temporal-success-story.md
Story workflow completed
```

## Key Learnings

1. **Azure Container Apps internal networking is limited** - External ingress is required for gRPC
2. **Port mapping is handled by ingress** - Always use port 443 for external services
3. **TLS is mandatory through Azure ingress** - Even with TLS termination
4. **Environment variables may reset on deployment** - Always verify after CI/CD runs
5. **Build arguments must be used correctly** - Dockerfile ARGs need proper handling

## Documentation Created

- `docs/sop/temporal-azure-configuration.md` - Complete setup guide
- `docs/sop/temporal-worker-postmortem.md` - Worker misconfiguration postmortem
- `docs/sop/temporal-azure-research.md` - Initial research document

## Files Modified

- `backend/Dockerfile` - Added WORKER_MODE support
- `backend/workflows/worker.py` - Added TLS support
- `backend/workflows/client.py` - Added TLS support
- `infra/modules/temporal-aca.bicep` - Fixed ingress configuration
- `infra/modules/worker-aca.bicep` - Removed incorrect probes

## Tags

temporal, azure, container-apps, grpc, tls, durable-workflows, story-generation, debugging, infrastructure
