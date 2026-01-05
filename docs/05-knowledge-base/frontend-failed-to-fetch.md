---
layout: default
title: "Troubleshooting Failed to fetch Error"
parent: "Knowledge Base"
---

# Troubleshooting "Failed to fetch" Error

## Issue
Frontend chat interface shows "Failed to fetch" when trying to interact with Marcus.

## Diagnosis

The backend is running and healthy:
- Health endpoint returns 200 OK
- Backend logs show successful requests
- Container app is running

The "Failed to fetch" error typically indicates:
1. **CORS issue** - Browser blocking the request
2. **Network connectivity** - Frontend can't reach backend
3. **Authentication token** - Token not being sent or invalid
4. **API URL misconfiguration** - Frontend pointing to wrong URL

## Quick Fixes

### 1. Check Frontend API URL
The frontend uses `VITE_API_URL` environment variable. Verify it's set correctly:

```bash
# Should be:
VITE_API_URL=https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io
# OR
VITE_API_URL=https://api.engram.work
```

### 2. Check Browser Console
Open browser DevTools (F12) and check:
- **Console tab** - Look for CORS errors or network errors
- **Network tab** - See if the request is being made and what the response is

### 3. Verify Authentication
- Check if you're logged in via MSAL
- Check if the token is being sent in the Authorization header
- Try logging out and logging back in

### 4. Check CORS Configuration
The backend CORS is configured in `backend/core/config.py`:
- Verify `CORS_ORIGINS` includes your frontend URL
- Check that credentials are allowed

## Common Solutions

### Solution 1: Clear Browser Cache
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

### Solution 2: Check Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Try sending a message
4. Look for the failed request
5. Check:
   - Request URL (is it correct?)
   - Request headers (is Authorization header present?)
   - Response status (what error code?)
   - Response body (what's the error message?)

### Solution 3: Verify API URL
Check what URL the frontend is using:
1. Open browser console
2. Type: `import.meta.env.VITE_API_URL`
3. Verify it matches the backend URL

### Solution 4: Test Direct API Call
Try calling the API directly from browser console:

```javascript
// Get token from MSAL
const account = msalInstance.getActiveAccount();
const tokenResponse = await msalInstance.acquireTokenSilent({
  scopes: [`api://94d50189-d4de-4b80-8804-2f3bf2e2d14f/user_impersonation`],
  account: account
});

// Test API call
fetch('https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${tokenResponse.accessToken}`
  },
  body: JSON.stringify({
    content: 'test',
    agent_id: 'marcus',
    session_id: 'test-session'
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

## Next Steps

If the issue persists:
1. Check backend logs for the specific request
2. Verify CORS configuration matches frontend origin
3. Check if authentication token is valid
4. Verify network connectivity between frontend and backend

## Related Files
- Frontend API client: `frontend/src/services/api.ts`
- Backend CORS config: `backend/core/config.py`
- Auth middleware: `backend/api/middleware/auth.py`

