---
layout: default
title: "Troubleshooting: Chat, VoiceLive, and Episodes Returning 401 Errors"
parent: "Knowledge Base"
---

# Troubleshooting: Chat, VoiceLive, and Episodes Returning 401 Errors

## Issue Summary

**Date**: December 28, 2025  
**Status**: 🔴 Critical - All three services down  
**Symptoms**: All API endpoints returning `401 Unauthorized`  
**Affected Services**:
- Chat API (`/api/v1/chat`)
- VoiceLive Health (`/api/v1/voice/health`)
- Episodes/Memory API (`/api/v1/memory/episodes`)

## Initial Symptoms

### Test Results
```bash
$ python3 scripts/test-api-direct.py

1️⃣ Testing Chat Endpoint (Model Router)...
   HTTP Status: 401 ❌ Chat failed

2️⃣ Testing Episodes/Memory API...
   HTTP Status: 401 ⚠️ Episodes API returned 401

3️⃣ Testing VoiceLive Health Check...
   HTTP Status: 401 ❌ VoiceLive health check failed
```

### Configuration Check
```bash
$ az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AUTH_REQUIRED']"

[
  {
    "name": "AUTH_REQUIRED",
    "value": "false"  # ✅ Correctly set
  }
]
```

**Observation**: `AUTH_REQUIRED=false` is set, but endpoints still return 401.

## Root Cause Analysis

### Investigation Steps

#### 1. Check Environment Variables
```bash
# Verify AUTH_REQUIRED is set correctly
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AUTH_REQUIRED']" \
  --output json
```

**Result**: ✅ `AUTH_REQUIRED=false` is correctly set

#### 2. Check Backend Logs
```bash
# Look for auth-related errors
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 100 --type console | grep -iE "(auth|401|AUTH_REQUIRED|bypass)"
```

**Result**: ❌ No auth-related logs found (suggests requests not reaching auth logic)

#### 3. Test Direct Container URL
```bash
# Bypass custom domain to test direct container
CONTAINER_FQDN=$(az containerapp show --name staging-env-api \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

curl -X POST "https://$CONTAINER_FQDN/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"model": "model-router", "messages": [{"role": "user", "content": "test"}]}'
```

**Result**: ❌ Still returns 401 (not a DNS/gateway issue)

#### 4. Check Code Logic
```python
# Test Pydantic conversion
from pydantic import Field
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    auth_required: bool = Field(True, alias="AUTH_REQUIRED")

s = TestSettings(AUTH_REQUIRED="false")
print(f"Value: {s.auth_required}, Type: {type(s.auth_required)}")
# Result: Value: False, Type: <class 'bool'> ✅ Correctly converts
```

**Result**: ✅ Pydantic correctly converts string "false" to boolean False

### Root Cause Identified

**Problem**: FastAPI's `Depends(security)` dependency is evaluated **BEFORE** the function body runs. Even with `auto_error=False`, the `HTTPBearer` security scheme was still being evaluated, which could cause issues.

**Code Flow**:
1. FastAPI evaluates `Depends(security)` → `HTTPBearer` runs
2. `HTTPBearer` processes Authorization header (even if missing)
3. Only then does `get_current_user()` function body execute
4. By this time, the security scheme may have already raised 401

## Solution Implemented

### Fix 1: Early Return Check (Initial Attempt)
```python
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> SecurityContext:
    # Check AUTH_REQUIRED first
    settings = get_settings()
    if not settings.auth_required:
        return SecurityContext(...)  # Return POC user
    # ... rest of auth logic
```

**Result**: ❌ Still failed - `Depends(security)` runs before function body

### Fix 2: Conditional Dependency (Final Solution)
```python
# Check AUTH_REQUIRED at module load time
def _get_auth_required() -> bool:
    settings = get_settings()
    auth_required_value = settings.auth_required
    return bool(auth_required_value) and str(auth_required_value).lower() != "false"

_AUTH_REQUIRED = _get_auth_required()
logger.info(f"🔐 Auth module loaded: AUTH_REQUIRED={_AUTH_REQUIRED}")

# No-op dependency when auth is disabled
async def _no_auth_dependency() -> None:
    return None

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security if _AUTH_REQUIRED else _no_auth_dependency
    ),
) -> SecurityContext:
    # Runtime check as fallback
    settings = get_settings()
    if not settings.auth_required or str(settings.auth_required).lower() == "false":
        logger.info("✅ Auth bypass enabled (AUTH_REQUIRED=false) - returning POC user")
        return SecurityContext(...)
    # ... rest of auth logic
```

**Result**: ✅ Bypasses `HTTPBearer` entirely when `AUTH_REQUIRED=false`

## Troubleshooting Steps

### Step 1: Verify Environment Configuration

```bash
#!/bin/bash
# scripts/verify-auth-config.sh

echo "🔍 Verifying Auth Configuration"
echo "=============================="

# Check AUTH_REQUIRED setting
echo ""
echo "1. Checking AUTH_REQUIRED environment variable:"
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AUTH_REQUIRED']" \
  --output json

# Check ENVIRONMENT setting
echo ""
echo "2. Checking ENVIRONMENT variable:"
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ENVIRONMENT']" \
  --output json

# Check if container is running
echo ""
echo "3. Checking container status:"
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "{name:name, status:properties.runningStatus, revision:properties.latestRevisionName}" \
  --output json
```

### Step 2: Test Endpoints

```bash
#!/bin/bash
# scripts/test-all-endpoints.sh

API_URL="https://api.engram.work"

echo "🧪 Testing All Endpoints"
echo "========================"

# Test Chat
echo ""
echo "1. Testing Chat Endpoint:"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -X POST "$API_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"model": "model-router", "messages": [{"role": "user", "content": "test"}], "session_id": "test-123"}'

# Test Episodes
echo ""
echo "2. Testing Episodes API:"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  "$API_URL/api/v1/memory/episodes?limit=5" \
  -H "Content-Type: application/json"

# Test VoiceLive Health
echo ""
echo "3. Testing VoiceLive Health:"
curl -s -w "\nHTTP Status: %{http_code}\n" \
  "$API_URL/api/v1/voice/health" \
  -H "Content-Type: application/json"
```

### Step 3: Check Backend Logs

```bash
#!/bin/bash
# scripts/check-auth-logs.sh

echo "📋 Checking Auth-Related Logs"
echo "============================="

# Check for auth module load
echo ""
echo "1. Auth module load messages:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 200 --type console 2>&1 | grep -iE "🔐|Auth module loaded|AUTH_REQUIRED" | tail -10

# Check for auth bypass messages
echo ""
echo "2. Auth bypass messages:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 200 --type console 2>&1 | grep -iE "✅|Auth bypass|poc-user" | tail -10

# Check for 401 errors
echo ""
echo "3. 401 Unauthorized errors:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 200 --type console 2>&1 | grep -iE "401|unauthorized|Missing.*token" | tail -10

# Check recent requests
echo ""
echo "4. Recent API requests:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 50 --type console 2>&1 | grep -iE "POST|GET.*/api/v1" | tail -10
```

### Step 4: Verify Code Deployment

```bash
#!/bin/bash
# scripts/verify-deployment.sh

echo "🚀 Verifying Deployment"
echo "======================"

# Check latest commit
echo ""
echo "1. Latest commit:"
git log -1 --oneline

# Check GitHub Actions status
echo ""
echo "2. GitHub Actions deployment status:"
gh run list --limit 1 --json status,conclusion,createdAt,headBranch \
  --jq '.[] | "Status: \(.status), Conclusion: \(.conclusion // "N/A"), Created: \(.createdAt)"'

# Check container revision
echo ""
echo "3. Active container revision:"
az containerapp revision list --name staging-env-api --resource-group engram-rg \
  --query "[0].{name:name, createdTime:properties.createdTime, active:properties.active}" \
  --output json

# Check if new code is running
echo ""
echo "4. Checking for new code indicators in logs:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 100 --type console 2>&1 | grep -iE "🔐|Auth module loaded|conditional" | tail -5
```

### Step 5: Force Container Restart

```bash
#!/bin/bash
# scripts/restart-backend.sh

echo "🔄 Restarting Backend Container"
echo "==============================="

# Get current revision
REVISION=$(az containerapp revision list --name staging-env-api \
  --resource-group engram-rg \
  --query "[0].name" -o tsv)

echo "Current revision: $REVISION"

# Restart
echo "Restarting..."
az containerapp revision restart \
  --name staging-env-api \
  --resource-group engram-rg \
  --revision "$REVISION"

echo "Waiting 30 seconds for container to restart..."
sleep 30

echo "✅ Container restarted"
```

## Diagnostic Scripts

### Complete Diagnostic

```bash
#!/bin/bash
# scripts/diagnose-401-errors.sh

echo "🔍 Complete Diagnostic for 401 Errors"
echo "======================================"

# Run all diagnostic steps
./scripts/verify-auth-config.sh
./scripts/test-all-endpoints.sh
./scripts/check-auth-logs.sh
./scripts/verify-deployment.sh

echo ""
echo "📊 Summary"
echo "=========="
echo "If all endpoints return 401:"
echo "  1. Verify AUTH_REQUIRED=false is set"
echo "  2. Check logs for '🔐 Auth module loaded' message"
echo "  3. Check logs for '✅ Auth bypass enabled' messages"
echo "  4. Verify latest code is deployed"
echo "  5. Restart container if needed"
```

## Expected Behavior After Fix

### When AUTH_REQUIRED=false

1. **Module Load**:
   ```
   🔐 Auth module loaded: AUTH_REQUIRED=False
   ```

2. **Request Handling**:
   ```
   Auth check: auth_required=False (type: bool), env=production, value=False
   ✅ Auth bypass enabled (AUTH_REQUIRED=false) - returning POC user
   ```

3. **Response**: All endpoints should return `200 OK` with data

### When AUTH_REQUIRED=true

1. **Module Load**:
   ```
   🔐 Auth module loaded: AUTH_REQUIRED=True
   ```

2. **Request Handling**:
   ```
   Auth check: auth_required=True (type: bool), env=production, value=True
   Auth required: True, proceeding with authentication
   ```

3. **Response**: Requires valid JWT token, returns 401 if missing/invalid

## Common Issues and Solutions

### Issue 1: AUTH_REQUIRED Not Being Read

**Symptoms**: Logs show `AUTH_REQUIRED=True` even though env var is `false`

**Solutions**:
1. Check for typos in environment variable name
2. Verify container app has the correct environment variable
3. Restart container to pick up changes
4. Check for settings caching (clear `@lru_cache` if needed)

### Issue 2: Code Not Deployed

**Symptoms**: Logs don't show new code indicators (e.g., "🔐 Auth module loaded")

**Solutions**:
1. Check GitHub Actions deployment status
2. Verify latest commit is deployed
3. Check container revision creation time
4. Force rebuild if needed

### Issue 3: HTTPBearer Still Running

**Symptoms**: 401 errors persist even with `AUTH_REQUIRED=false`

**Solutions**:
1. Verify conditional dependency is working
2. Check logs for "Auth module loaded" message
3. Ensure `_no_auth_dependency` is being used
4. Restart container to reload module

### Issue 4: Settings Caching

**Symptoms**: Changes to `AUTH_REQUIRED` not taking effect

**Solutions**:
1. Restart container (clears `@lru_cache`)
2. Check if Key Vault is overriding settings
3. Verify environment variable is set correctly
4. Add explicit cache clearing if needed

## Prevention

### Best Practices

1. **Always Test After Deployment**:
   ```bash
   python3 scripts/test-api-direct.py
   ```

2. **Monitor Logs**:
   ```bash
   az containerapp logs show --name staging-env-api --resource-group engram-rg \
     --tail 50 --type console | grep -iE "auth|401"
   ```

3. **Verify Configuration**:
   ```bash
   ./scripts/verify-auth-config.sh
   ```

4. **Document Changes**: Update this document when making auth-related changes

## Related Documentation

- [Enterprise Auth Robustness Plan](../sop/enterprise-auth-robustness-plan.md)
- [Secrets Management SOP](../sop/secrets-management.md)
- [Azure AI Configuration](../sop/azure-ai-configuration.md)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-28 | Initial documentation | System |
| 2025-12-28 | Added conditional dependency fix | System |
| 2025-12-28 | Added diagnostic scripts | System |

