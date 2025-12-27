# Fix Voice Connection "Failed to fetch" Error

## Problem
The voice connection is failing with "Failed to fetch" error when trying to connect to the backend API.

## Root Cause
The diagnostic shows that the `/api/v1/voice/realtime/token` endpoint is returning **401 Unauthorized**, which means authentication is required but the frontend is not sending authentication tokens.

## Solution Options

### Option 1: Disable Authentication for Voice Endpoints (POC/Development)

If this is a POC or development environment, you can disable authentication:

```bash
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars 'AUTH_REQUIRED=false'
```

**Note:** This makes the API publicly accessible without authentication. Only use this in development/POC environments.

### Option 2: Add Authentication to Frontend (Production)

For production, you need to implement authentication in the frontend:

1. **Get authentication token** (Entra ID token or dev token)
2. **Store token** in localStorage or auth context
3. **Send token** with API requests

The API client already supports this - it reads from `localStorage.getItem('auth_token')`.

### Option 3: Make Voice Endpoints Public (Recommended for Voice)

Since voice endpoints need to be accessible from the browser without complex auth flows, you can make them public while keeping other endpoints protected.

**Backend Change Required:**
Modify `backend/api/routers/voice.py` to make the token endpoint public:

```python
from backend.api.middleware.auth import get_current_user, get_optional_user

@router.post("/realtime/token", response_model=TokenResponse)
async def get_realtime_token(
    request: TokenRequest,
    user: Optional[SecurityContext] = Depends(get_optional_user)  # Optional auth
):
    # ... existing code ...
```

Then add a helper function in `backend/api/middleware/auth.py`:

```python
async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[SecurityContext]:
    """Get current user if authenticated, otherwise return None"""
    settings = get_settings()
    if not settings.auth_required:
        return None
    
    try:
        return await get_current_user(request, credentials)
    except:
        return None  # Allow unauthenticated access
```

## Quick Fix (Immediate)

For immediate testing, disable authentication:

```bash
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars 'AUTH_REQUIRED=false'
```

Then wait a few seconds for the container to restart and try the voice connection again.

## Verification

After applying the fix, test the connection:

```bash
# Test the endpoint
curl -X POST https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/voice/realtime/token \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"elena","session_id":"test"}'
```

You should get a JSON response with `token` and `endpoint` fields instead of 401.

## CORS Note

The CORS configuration is already correct:
- `https://engram.work` is in the allowed origins
- The wildcard `*` is also included

If you still see CORS errors after fixing authentication, check that the frontend is using the correct API URL.


