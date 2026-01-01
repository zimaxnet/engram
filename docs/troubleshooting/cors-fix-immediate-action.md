# CORS Fix - Immediate Action Required

**Status:** CORS errors blocking all API access  
**Root Cause:** `CORS_ORIGINS` environment variable in Azure Container Apps doesn't include `https://engram.work`

---

## Immediate Fix (No Code Deployment Needed)

The CORS error indicates that `https://engram.work` is not in the `CORS_ORIGINS` environment variable in Azure Container Apps.

### Step 1: Find the Correct Container App Name

```bash
az containerapp list --resource-group zimax-ai --query "[].name" -o table
```

Look for the backend API container app (likely named something like `staging-env-api` or similar).

### Step 2: Check Current CORS_ORIGINS

```bash
# Replace <container-app-name> with the actual name from Step 1
az containerapp show \
  --name <container-app-name> \
  --resource-group zimax-ai \
  --query "properties.template.containers[0].env[?name=='CORS_ORIGINS']" \
  --output table
```

### Step 3: Update CORS_ORIGINS

If `https://engram.work` is missing, update it:

```bash
az containerapp update \
  --name <container-app-name> \
  --resource-group zimax-ai \
  --set-env-vars \
    CORS_ORIGINS='["https://engram.work","http://localhost:5173","http://localhost:5174"]'
```

**Or via Azure Portal:**

1. Go to Azure Portal → Container Apps
2. Find your backend API container app
3. Go to **Configuration** → **Environment variables**
4. Find `CORS_ORIGINS`
5. Update value to: `["https://engram.work","http://localhost:5173","http://localhost:5174"]`
6. Click **Save**
7. Container will restart automatically

### Step 4: Verify Fix

After the container restarts (usually 30-60 seconds):

1. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)
2. **Reload** `https://engram.work`
3. **Check browser console** - CORS errors should be gone
4. **Test API calls** - Episodes, chat, etc. should work

---

## Expected Behavior After Fix

**Browser Network Tab for OPTIONS request should show:**
```
Status: 200 OK
Response Headers:
  Access-Control-Allow-Origin: https://engram.work
  Access-Control-Allow-Credentials: true
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
  Access-Control-Allow-Headers: authorization, content-type
```

**Browser Console:**
- ✅ No CORS errors
- ✅ API calls succeed
- ✅ Episodes load
- ✅ Chat works

---

## Why This Works

The `CORSPreflightMiddleware` checks if the origin (`https://engram.work`) is in the `CORS_ORIGINS` list. If it's not, it returns 200 OK but **without** the `Access-Control-Allow-Origin` header, which causes the browser to block the request (this is correct security behavior).

By adding `https://engram.work` to `CORS_ORIGINS`, the middleware will add the required CORS headers, allowing the browser to complete the request.

---

## Configuration Reference

**Correct CORS_ORIGINS value:**
```json
["https://engram.work","http://localhost:5173","http://localhost:5174"]
```

**As environment variable string:**
```
CORS_ORIGINS=["https://engram.work","http://localhost:5173","http://localhost:5174"]
```

**Infrastructure template already has this:** `infra/modules/backend-aca.bicep` line 278

---

## If Update Doesn't Work

1. **Check container logs** to see what CORS_ORIGINS value is being used:
   ```bash
   az containerapp logs show \
     --name <container-app-name> \
     --resource-group zimax-ai \
     --tail 100 \
     --follow
   ```

2. **Look for** `CORS preflight request` log messages to see what origin is being checked

3. **Verify** the environment variable was actually updated:
   ```bash
   az containerapp show \
     --name <container-app-name> \
     --resource-group zimax-ai \
     --query "properties.template.containers[0].env[?name=='CORS_ORIGINS']" \
     --output json
   ```

---

## Related Documentation

- `docs/troubleshooting/cors-errors-january-2026.md` - Detailed troubleshooting
- `backend/api/middleware/cors_preflight.py` - CORS middleware implementation
- `backend/core/config.py` - CORS_ORIGINS configuration

