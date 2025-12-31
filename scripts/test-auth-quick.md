# Quick Authentication Test Guide

## Prerequisites

1. **Get an authentication token** after logging in with Google:
   - Open browser DevTools (F12)
   - Go to Application > Local Storage
   - Look for MSAL tokens (keys like `msal.{clientId}.idtoken`)
   - Or check Network tab for Authorization header in API requests

## Test Commands

### Test with Token

```bash
# Set your token
export AUTH_TOKEN='your-token-here'

# Run comprehensive test
./scripts/test-authentication-fix.sh
```

### Test Individual Endpoints

```bash
# Chat
curl -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello", "agent_id": "elena"}' \
  https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/chat

# Episodes
curl -H "Authorization: Bearer $AUTH_TOKEN" \
  https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/memory/episodes

# Stories
curl -H "Authorization: Bearer $AUTH_TOKEN" \
  https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/story/

# Voice Token
curl -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "elena"}' \
  https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/voice/realtime/token
```

### Diagnose Token Issues

```bash
AUTH_TOKEN='your-token' python3 scripts/diagnose-auth-token.py
```

## Expected Results

✅ **All endpoints should return 200 OK** (not 401 Unauthorized)

If you see 401 errors, check:
1. Token is not expired
2. Token has correct audience (`api://{CLIENT_ID}`)
3. Token issuer is valid Azure CIAM
4. Backend logs for specific error messages
