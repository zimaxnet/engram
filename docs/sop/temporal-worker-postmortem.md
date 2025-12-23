# Temporal Worker Container Misconfiguration

> **Incident Date**: December 22-23, 2025  
> **Status**: Resolved  
> **Impact**: Story generation (Sage) non-functional; Temporal workflows never executed

## Summary

The Temporal worker container was running as a duplicate API server instead of the Temporal worker process. This caused all Temporal workflows (story generation, agent conversations) to timeout because no worker was polling the task queue.

## Root Cause

The CI pipeline built the worker image using:

```yaml
# .github/workflows/ci.yml
- name: Build and push worker image
  uses: docker/build-push-action@v5
  with:
    context: ./backend
    file: ./backend/Dockerfile
    build-args: |
      WORKER_MODE=true  # ← This was ignored!
```

However, the `backend/Dockerfile` did NOT handle the `WORKER_MODE` build argument:

```dockerfile
# BEFORE (broken)
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

The build argument was passed but never used. The result:

- `ghcr.io/zimaxnet/engram/worker:latest` contained the same CMD as the API
- Worker container started Uvicorn on port 8080
- No process was polling the `engram-agents` Temporal task queue
- All workflow.execute() calls timed out

## Symptoms

1. **Story creation returned "Backend call failure"** after ~45 second timeout
2. **API logs showed**: `"Creating story via Temporal: <topic>"` but no completion
3. **Worker logs showed**: `Uvicorn running on http://0.0.0.0:8080` (wrong!)
4. **Worker logs should show**: `Starting worker on task queue: engram-agents`
5. **Temporal Server healthy** with no errors, just idle task queues

## Detection

```bash
# Check what worker is running
az containerapp logs show --name staging-env-worker --resource-group engram-rg --type console --tail 20

# Expected (correct):
# "Connecting to Temporal at..."
# "Starting worker on task queue: engram-agents"
# "Worker started successfully"

# Actual (broken):
# "Started server process [1]"
# "Uvicorn running on http://0.0.0.0:8080"
```

## Resolution

### 1. Updated Dockerfile to Support WORKER_MODE

```dockerfile
# AFTER (fixed)
ARG WORKER_MODE=false
ENV WORKER_MODE=${WORKER_MODE}

# Create entrypoint script
RUN printf '#!/bin/bash\n\
set -e\n\
if [ "$WORKER_MODE" = "true" ]; then\n\
    echo "Starting Temporal Worker..."\n\
    exec python -m backend.workflows.worker\n\
else\n\
    echo "Starting API Server..."\n\
    exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8080\n\
fi\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
```

### 2. Updated Worker Infrastructure

Removed HTTP probe and ingress from `worker-aca.bicep`:

```bicep
// Worker doesn't expose HTTP - no ingress or probes needed
configuration: {
  // ingress removed
  dapr: { enabled: false }
}
```

## Lessons Learned

### 1. Build Arguments Must Be Used

> **Rule**: If you pass a build argument, the Dockerfile MUST use it.

Build arguments (`ARG`) are only available at build time. If you don't:

- Convert to ENV: `ENV WORKER_MODE=${WORKER_MODE}`
- Use in RUN or CMD: They have no effect at runtime

### 2. Verify Container Behavior, Not Just Deployment

> **Rule**: After deployment, verify the container is doing what you expect.

Check container logs immediately after deployment:

```bash
az containerapp logs show --name <app> --resource-group <rg> --type console --tail 20
```

Look for the **startup message** that confirms correct mode.

### 3. Don't Reuse Dockerfiles Without Modification

> **Rule**: Separate concerns with separate Dockerfiles, or add clear mode switching.

Options:

- **Option A**: Separate `Dockerfile.api` and `Dockerfile.worker`
- **Option B**: Single Dockerfile with clear ARG/ENV handling (chosen approach)
- **Option C**: Override CMD in container deployment (fragile)

### 4. Workers Don't Need HTTP Probes

> **Rule**: Background workers should use process-based health checks.

```dockerfile
# For workers (process check)
HEALTHCHECK CMD pgrep -f "workflows.worker" || exit 1

# For APIs (HTTP check)
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
```

### 5. Log First Startup Message Explicitly

> **Rule**: The first log line should identify what mode the container is running.

```python
# worker.py
logger.info(f"Starting worker on task queue: {settings.temporal_task_queue}")

# main.py  
logger.info(f"Starting Engram API v{__version__}")
```

This makes logs immediately diagnostic.

## Verification Checklist

After deploying worker changes, verify:

- [ ] Worker logs show "Starting Temporal Worker..."
- [ ] Worker logs show "Connected to Temporal namespace: default"
- [ ] Worker logs show "Starting worker on task queue: engram-agents"
- [ ] Worker logs show "Worker started successfully"
- [ ] Story creation returns success (not timeout)
- [ ] Temporal UI shows workflows executing (not stuck in pending)

## Related Files

| File | Purpose |
|------|---------|
| [Dockerfile](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/Dockerfile) | Container entry point logic |
| [worker.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/workflows/worker.py) | Temporal worker main loop |
| [ci.yml](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/.github/workflows/ci.yml#L74-L86) | Worker image build configuration |
| [worker-aca.bicep](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/infra/modules/worker-aca.bicep) | Azure Container App infrastructure |
