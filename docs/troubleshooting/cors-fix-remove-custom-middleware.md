# CORS Fix - Remove Custom Preflight Middleware

**Date:** January 1, 2026  
**Status:** Fix implemented

---

## Problem

CORS errors persist because:
1. `CORSPreflightMiddleware` intercepts OPTIONS requests FIRST (due to reverse middleware execution order)
2. It returns early, so `CORSMiddleware` NEVER processes OPTIONS requests
3. If `CORSPreflightMiddleware` has bugs or origin validation fails, no CORS headers are added
4. Browser blocks requests due to missing `Access-Control-Allow-Origin` header

---

## Root Cause

In Starlette/FastAPI, middleware executes in **REVERSE order** of addition:

**Current Code:**
```python
app.add_middleware(CORSMiddleware, ...)      # Added FIRST
app.add_middleware(CORSPreflightMiddleware)  # Added SECOND
```

**Execution Order (reverse):**
1. `CORSPreflightMiddleware` executes FIRST
2. `CORSMiddleware` executes SECOND (but never gets OPTIONS requests)

**The Issue:**
- `CORSPreflightMiddleware` returns early for OPTIONS requests
- `CORSMiddleware` never processes them
- If custom middleware has issues, CORS fails completely

---

## Solution

**Remove `CORSPreflightMiddleware` and rely on FastAPI's `CORSMiddleware`.**

FastAPI's `CORSMiddleware` is designed to handle OPTIONS requests correctly:
- It processes OPTIONS at the **middleware level** (before route dependencies)
- Route dependencies (like `get_current_user`) are **NOT evaluated** for OPTIONS
- This is the standard, recommended approach

---

## Changes Made

### File: `backend/api/main.py`

**Removed:**
```python
from .middleware.cors_preflight import CORSPreflightMiddleware
app.add_middleware(CORSPreflightMiddleware)
```

**Updated comments:**
```python
# CORS middleware (handles preflight OPTIONS requests automatically)
# CORSMiddleware processes OPTIONS requests at the middleware level,
# before route dependencies (like get_current_user) are evaluated,
# so it doesn't require authentication for preflight requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Why This Works

1. **CORSMiddleware handles OPTIONS automatically** - No custom middleware needed
2. **Middleware-level processing** - OPTIONS requests are handled before route dependencies
3. **No authentication required** - Route dependencies aren't evaluated for OPTIONS
4. **Standard approach** - This is how FastAPI/Starlette CORS is intended to work
5. **Simpler code** - Less code to maintain, fewer potential bugs

---

## Why CORSPreflightMiddleware Was Added

Originally, `CORSPreflightMiddleware` was added because it was believed that:
- Route dependencies were being evaluated before CORSMiddleware could intercept OPTIONS
- Custom middleware was needed to bypass authentication

However, FastAPI's `CORSMiddleware` already handles this correctly. The custom middleware was actually causing more problems than it solved.

---

## Important: CORS_ORIGINS Configuration

**CRITICAL:** Ensure `CORS_ORIGINS` environment variable in Azure Container Apps includes `https://engram.work`:

```bash
CORS_ORIGINS=["https://engram.work","http://localhost:5173","http://localhost:5174"]
```

**Check current value:**
```bash
az containerapp show \
  --name <container-app-name> \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env[?name=='CORS_ORIGINS']" \
  --output table
```

**Update if needed:**
```bash
az containerapp update \
  --name <container-app-name> \
  --resource-group zimax-ai \
  --set-env-vars \
    CORS_ORIGINS='["https://engram.work","http://localhost:5173","http://localhost:5174"]'
```

---

## Testing

After deployment:

1. **Clear browser cache** (Ctrl+Shift+R / Cmd+Shift+R)
2. **Open browser DevTools → Network tab**
3. **Make a request from `https://engram.work`**
4. **Check OPTIONS preflight request:**
   - Status: `200 OK`
   - Headers should include:
     - `Access-Control-Allow-Origin: https://engram.work`
     - `Access-Control-Allow-Credentials: true`
     - `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH`
     - `Access-Control-Allow-Headers: authorization, content-type`

---

## Expected Behavior

**Before Fix:**
- ❌ OPTIONS preflight: Missing `Access-Control-Allow-Origin` header
- ❌ Browser blocks request
- ❌ CORS errors in console

**After Fix:**
- ✅ OPTIONS preflight: Returns 200 OK with CORS headers
- ✅ Browser allows request
- ✅ API calls succeed

---

## Related Files

- `backend/api/main.py` - Middleware configuration (updated)
- `backend/api/middleware/cors_preflight.py` - Custom middleware (no longer used, can be removed in future cleanup)
- `backend/core/config.py` - CORS_ORIGINS configuration
- `infra/modules/backend-aca.bicep` - Infrastructure template (CORS_ORIGINS should be set here)

---

## Migration Notes

The `CORSPreflightMiddleware` file (`backend/api/middleware/cors_preflight.py`) is no longer used but hasn't been deleted yet. It can be removed in a future cleanup commit if desired.

