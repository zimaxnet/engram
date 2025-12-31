# How to Get Authentication Token from Browser

## Method 1: Browser DevTools - Local Storage

1. Open your browser DevTools (F12 or Right-click > Inspect)
2. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click on **Local Storage** in the left sidebar
4. Click on your site's domain (e.g., `engram.work` or `localhost:5173`)
5. Look for keys starting with `msal.` or containing `token` or `access`
6. Common keys:
   - `msal.{clientId}.idtoken`
   - `msal.{clientId}.accesstoken.{scope}`
   - `msal.account.keys`
7. Copy the token value (it's a long JWT string)

## Method 2: Browser DevTools - Network Tab

1. Open DevTools (F12)
2. Go to the **Network** tab
3. Make an API request (e.g., send a chat message)
4. Find the request to `/api/v1/chat` or similar
5. Click on the request
6. Go to the **Headers** tab
7. Look for `Authorization: Bearer {token}`
8. Copy the token (everything after "Bearer ")

## Method 3: Browser Console

Open the browser console and run:

```javascript
// Get MSAL instance
const msalInstance = window.msalInstance || window.msal;

// Get current account
const account = msalInstance?.getAllAccounts()?.[0];

if (account) {
  // Request token
  msalInstance.acquireTokenSilent({
    scopes: ['api://YOUR_CLIENT_ID/user_impersonation'],
    account: account
  }).then(response => {
    console.log('Access Token:', response.accessToken);
    // Copy this token
  });
}
```

## Quick Test

Once you have the token, run:

```bash
export AUTH_TOKEN='your-token-here'
./scripts/test-authentication-fix.sh
```
