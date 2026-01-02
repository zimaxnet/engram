---
title: CORS Configuration SOP
nav_order: 1
parent: Troubleshooting
---

# CORS Configuration - Standard Operating Procedure

> **Last Updated:** 2026-01-02  
> **Status:** Production

This SOP documents the CORS configuration for Engram and how to diagnose and fix CORS errors.

---

## Quick Fix Checklist

If you see "No 'Access-Control-Allow-Origin' header is present":

1. **Verify `CORS_ORIGINS` includes your frontend URL**

   ```bash
   az containerapp show --name staging-env-api --resource-group engram-rg \
     --query "properties.template.containers[0].env[?name=='CORS_ORIGINS']" -o table
   ```

   Must include: `https://engram.work`

2. **Verify Azure Platform Auth is DISABLED**

   ```bash
   az containerapp auth show --name staging-env-api --resource-group engram-rg
   ```

   Must return:

   ```json
   "platform": {
     "enabled": false
   }
   ```

   If enabled:

   ```bash
   az containerapp auth update --name staging-env-api --resource-group engram-rg \
     --enabled false --action AllowAnonymous
   ```

3. **Verify `CORSPreflightMiddleware` is registered in `main.py`**

   ```bash
   grep -n "CORSPreflightMiddleware" backend/api/main.py
   ```

   Must show import AND `app.add_middleware(CORSPreflightMiddleware)`

4. **If missing, add the middleware:**

   ```python
   from .middleware.cors_preflight import CORSPreflightMiddleware
   # ... later in create_app() ...
   app.add_middleware(CORSPreflightMiddleware)
   ```

5. **Deploy and test**

   ```bash
   git add . && git commit -m "fix(cors): ensure middleware is registered"
   git push
   ```

---

## Architecture

### Middleware Stack (Execution Order)

```
Request → ProxyHeaders → Telemetry → Logging → CORSPreflight → CORSMiddleware → Routes
```

| Middleware | Purpose |
|------------|---------|
| `CORSMiddleware` | FastAPI built-in, adds CORS headers to responses |
| `CORSPreflightMiddleware` | Intercepts OPTIONS requests before auth |
| `RequestLoggingMiddleware` | Logs request/response details |
| `TelemetryMiddleware` | OpenTelemetry tracing |
| `ProxyHeadersMiddleware` | Handles X-Forwarded-* from load balancer |

### Key Files

| File | Purpose |
|------|---------|
| `backend/api/main.py` | Middleware registration |
| `backend/api/middleware/cors_preflight.py` | OPTIONS handler |
| `backend/core/config.py` | `CORS_ORIGINS` setting |
| `infra/modules/backend-aca.bicep` | Azure deployment config |

---

## Configuration

### Environment Variable: `CORS_ORIGINS`

**Format:** JSON array as string

**Production value:**

```
["https://engram.work","http://localhost:5173","http://localhost:5174"]
```

**Set in:** `infra/modules/backend-aca.bicep` line 277-279

**Code default:** Only localhost (see `config.py` line 140)

---

## Common Issues

### Issue 1: Middleware Not Registered

**Symptom:** CORS errors despite correct `CORS_ORIGINS`

**Cause:** `CORSPreflightMiddleware` exists but not imported/added

**Fix:** Add to `main.py`:

```python
from .middleware.cors_preflight import CORSPreflightMiddleware
# ... in create_app() ...
app.add_middleware(CORSPreflightMiddleware)
```

### Issue 2: Missing Origin in CORS_ORIGINS

**Symptom:** CORS works locally but fails in production

**Cause:** Production URL not in `CORS_ORIGINS`

**Fix:** Update Bicep or directly via Azure CLI:

```bash
az containerapp update --name staging-env-api --resource-group engram-rg \
  --set-env-vars 'CORS_ORIGINS=["https://engram.work","http://localhost:5173"]'
```

### Issue 3: Auth Blocking OPTIONS

**Symptom:** OPTIONS returns 401 Unauthorized

**Cause:** Auth middleware runs before CORS handler

**Fix:** Ensure `CORSPreflightMiddleware` is added AFTER `CORSMiddleware` (runs before in execution order)

### Issue 4: Azure Platform Auth (Easy Auth) Enabled

**Symptom:** OPTIONS returns 401 Unauthorized or 302 Redirect before reaching app logs

**Cause:** Azure Container Apps "Authentication and Authorization" feature intercepts requests.

**Fix:** Disable Platform Auth via CLI (or ensure Bicep `authConfigs` resource is correctly applied):

```bash
az containerapp auth update --name staging-env-api --resource-group engram-rg \
  --enabled false --action AllowAnonymous
```

---

## Testing

### CLI Test

```bash
curl -I -X OPTIONS https://api.engram.work/api/v1/chat \
  -H "Origin: https://engram.work" \
  -H "Access-Control-Request-Method: POST"
```

**Expected headers:**

```
HTTP/2 200
Access-Control-Allow-Origin: https://engram.work
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: POST
```

### Browser Test

1. Open `https://engram.work`
2. DevTools → Network → Filter "OPTIONS"
3. Send a chat message
4. Verify OPTIONS returns 200 with CORS headers

---

## Related Documentation

- [Authentication Guide](authentication-guide.md)
- [Deployment Conflicts](deployment-conflicts.md)
- [CORS Errors January 2026](cors-errors-january-2026.md)
