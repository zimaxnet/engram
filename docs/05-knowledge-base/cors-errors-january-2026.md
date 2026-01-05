---
layout: default
title: "CORS Errors - January 1, 2026"
parent: "Knowledge Base"
---

# CORS Errors - January 1, 2026

**Status:** Active CORS errors preventing frontend from accessing API  
**Error:** "No 'Access-Control-Allow-Origin' header is present on the requested resource"

---

## Current Error

```
Access to fetch at 'https://api.engram.work/api/v1/memory/episodes/session-...' 
from origin 'https://engram.work' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**Chat also failing:** "Failed to fetch" error

---

## Root Cause Analysis

The CORS error indicates that:
1. Browser is making a preflight OPTIONS request
2. Backend is not returning `Access-Control-Allow-Origin` header
3. This suggests either:
   - `https://engram.work` is not in `CORS_ORIGINS` environment variable
   - CORS middleware is not working correctly
   - Deployment hasn't completed with CORS fix

---

## Deployment Status

- ✅ **Latest successful deployment:** 2026-01-01T01:31:29Z
- ❌ **Latest deployment:** 2026-01-01T01:32:57Z (FAILED - active deployment conflict)
- ⏳ **Current status:** Old code running (deployment conflicts preventing updates)

---

## Solution

### Step 1: Verify CORS_ORIGINS in Azure Container Apps

The `CORS_ORIGINS` environment variable must include `https://engram.work`:

```bash
az containerapp show \
  --name staging-env-api \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env[?name=='CORS_ORIGINS']" \
  --output table
```

**Expected value:**
```
CORS_ORIGINS=["https://engram.work","http://localhost:5173","http://localhost:5174"]
```

Or as a JSON string:
```
CORS_ORIGINS=["https://engram.work","http://localhost:5173","http://localhost:5174"]
```

### Step 2: Update CORS_ORIGINS if Missing

If `https://engram.work` is not in the list:

```bash
az containerapp update \
  --name staging-env-api \
  --resource-group zimax-ai \
  --set-env-vars \
    CORS_ORIGINS='["https://engram.work","http://localhost:5173","http://localhost:5174"]'
```

**Or via Azure Portal:**
1. Azure Portal → Container Apps → `staging-env-api`
2. Configuration → Environment variables
3. Edit `CORS_ORIGINS`
4. Set to: `["https://engram.work","http://localhost:5173","http://localhost:5174"]`
5. Save

### Step 3: Wait for Active Deployment to Complete

The failed deployment was blocked by an active deployment. Wait for it to complete or check status:

```bash
gh run list --workflow=deploy.yml --limit 1
```

### Step 4: Verify CORS Middleware Code

The code includes:
- ✅ `CORSMiddleware` (FastAPI built-in)
- ✅ `CORSPreflightMiddleware` (custom - handles OPTIONS before auth)
- ✅ Exception handlers (add CORS headers to errors)

**Code location:** `backend/api/main.py` and `backend/api/middleware/cors_preflight.py`

---

## Configuration Reference

### Default CORS_ORIGINS (Code)

**File:** `backend/core/config.py`

```python
cors_origins: list[str] = Field(
    default=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"], 
    alias="CORS_ORIGINS"
)
```

**Note:** Default does NOT include `https://engram.work` - must be set via environment variable!

### Required CORS_ORIGINS (Production)

```bash
CORS_ORIGINS=["https://engram.work","http://localhost:5173","http://localhost:5174","http://localhost:3000"]
```

**Format:** JSON array as a string

---

## How CORS Works in This App

1. **CORSMiddleware** (FastAPI built-in):
   - Handles CORS headers for all requests
   - Processes OPTIONS preflight requests

2. **CORSPreflightMiddleware** (Custom):
   - Runs BEFORE authentication
   - Intercepts OPTIONS requests
   - Returns 200 OK with CORS headers immediately
   - Prevents auth middleware from blocking preflight

3. **Exception Handlers**:
   - Add CORS headers to error responses (400, 401, 422, etc.)
   - Ensures browser can read error messages

**Middleware Order:**
1. CORSMiddleware (added first)
2. CORSPreflightMiddleware (added second, runs first - intercepts OPTIONS)
3. RequestLoggingMiddleware
4. TelemetryMiddleware
5. ProxyHeadersMiddleware
6. Auth middleware (via dependencies)

---

## Testing

After updating `CORS_ORIGINS`:

1. **Wait for container restart** (automatic when env var changes)
2. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)
3. **Test in browser:**
   - Open `https://engram.work`
   - Open DevTools → Network tab
   - Try to load episodes or send chat message
   - Check that OPTIONS request returns 200 with CORS headers

4. **Check response headers:**
   ```
   Access-Control-Allow-Origin: https://engram.work
   Access-Control-Allow-Credentials: true
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
   Access-Control-Allow-Headers: authorization, content-type
   ```

---

## Quick Fix (If Deployed Code is Correct)

If the code is correct but `CORS_ORIGINS` is wrong:

1. Update environment variable in Azure (see Step 2 above)
2. Container will restart automatically
3. Test immediately - no code deployment needed

---

## Related Documentation

- `docs/troubleshooting/authentication-cors-complete-fix.md` - Original CORS fix
- `backend/api/middleware/cors_preflight.py` - CORS preflight middleware
- `backend/api/main.py` - Middleware configuration
- `backend/core/config.py` - CORS_ORIGINS configuration

