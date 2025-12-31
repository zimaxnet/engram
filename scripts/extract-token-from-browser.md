# How to Extract JWT Token from Browser

## Quick Method (Recommended)

1. **Open Browser DevTools** (F12)
2. **Go to Console tab**
3. **Paste this JavaScript code:**

```javascript
// Get MSAL instance (adjust if your app uses a different variable)
const msalInstance = window.msalInstance || window.msal;

// Get all accounts
const accounts = msalInstance?.getAllAccounts() || [];

if (accounts.length === 0) {
  console.log("❌ No accounts found. Make sure you're logged in.");
} else {
  const account = accounts[0];
  console.log("✅ Account found:", account.username);
  
  // Request access token
  msalInstance.acquireTokenSilent({
    scopes: ['api://e32c6c40-615e-4a25-bc9e-944169e99697/user_impersonation'],
    account: account
  }).then(response => {
    console.log("✅ Access Token:");
    console.log(response.accessToken);
    console.log("\n📋 Copy this token for testing:");
    console.log(response.accessToken);
  }).catch(error => {
    console.error("❌ Error getting token:", error);
  });
}
```

4. **Copy the token** from the console output
5. **Use it in test script:**

```bash
python3 scripts/test-chat-debug.py --token "YOUR_TOKEN_HERE" --message "hi"
```

## Alternative: Network Tab Method

1. **Open DevTools** (F12)
2. **Go to Network tab**
3. **Send a chat message** in the app
4. **Find the request** to `/api/v1/chat`
5. **Click on the request**
6. **Go to Headers tab**
7. **Look for `Authorization: Bearer ...`**
8. **Copy the token** (everything after "Bearer ")

## Alternative: Application Tab (Local Storage)

The MSAL cache keys you provided are just keys, not the tokens. The actual tokens are stored as **values** in Local Storage:

1. **Open DevTools** (F12)
2. **Go to Application tab** (Chrome) or **Storage tab** (Firefox)
3. **Click Local Storage** → `https://engram.work`
4. **Look for the key:** `msal.2|d240186f-f80e-4369-9296-57fef571cd93.6684288a-b805-4161-bf41-ba2121e51c90|engramai.ciamlogin.com|accesstoken|e32c6c40-615e-4a25-bc9e-944169e99697|6684288a-b805-4161-bf41-ba2121e51c90|api://e32c6c40-615e-4a25-bc9e-944169e99697/user_impersonation||`
5. **Copy the VALUE** (it's a JSON object containing the actual JWT token)

The value will be a JSON object like:
```json
{
  "credentialType": "AccessToken",
  "secret": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs...",
  ...
}
```

The `secret` field contains the actual JWT token.

