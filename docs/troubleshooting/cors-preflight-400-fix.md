# CORS Preflight 400 Error Fix

## Issue

OPTIONS preflight requests are returning `400 Bad Request` with header `x-ms-middleware-request-id`, indicating Azure Container Apps is rejecting the request before it reaches the FastAPI application.

## Root Cause

The 400 error with `x-ms-middleware-request-id` suggests Azure Container Apps or Azure Front Door is rejecting the OPTIONS request before it reaches the application.

## Solution

1. **Code Fix**: Added `CORSPreflightMiddleware` to ensure OPTIONS requests are handled correctly
2. **Azure Configuration**: Verify Azure Container Apps ingress configuration allows OPTIONS requests

## Testing

After deployment, test with:

```bash
curl -v -X OPTIONS \
  -H "Origin: https://engram.work" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  https://api.engram.work/api/v1/chat
```

Expected: `200 OK` with CORS headers, not `400 Bad Request`

## If Issue Persists

Check Azure Container Apps logs:
```bash
az containerapp logs show \
  --name staging-env-api \
  --resource-group engram-rg \
  --tail 100 \
  --type console | grep -iE "(options|cors|400)"
```

The fix is committed and will be deployed after the current deployment completes.
