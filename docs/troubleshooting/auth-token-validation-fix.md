# Authentication Token Validation Fix

## Problem Summary

After Google login works successfully, the backend API was rejecting tokens with 401 Unauthorized errors. This prevented chat, voice, episodes, and stories from working.

## Root Cause

The authentication middleware was using a **pre-configured JWKS endpoint** based on the tenant domain and ID. However, Azure CIAM issues tokens with **GUID-based issuers** that may differ from the configured endpoint. The middleware couldn't find the correct signing keys because:

1. **JWKS Endpoint Mismatch**: The configured JWKS endpoint (`https://engramai.ciamlogin.com/{tenant_id}/discovery/v2.0/keys`) might not match the token's actual issuer
2. **Token Issuer Format**: Azure CIAM issues tokens with issuers like `https://{GUID}.ciamlogin.com/{GUID}/v2.0`, which requires fetching JWKS from that specific issuer's endpoint
3. **Key Lookup Failure**: The signing key (KID) in the token header couldn't be found in the JWKS fetched from the wrong endpoint

## Solution

Updated the authentication middleware to follow **standard JWT validation practices**:

1. **Decode token first** (without verification) to extract the issuer
2. **Derive JWKS endpoint** from the token's issuer: `{issuer}/discovery/v2.0/keys`
3. **Fetch JWKS from token's issuer** (proper JWT validation)
4. **Fallback to configured endpoint** if issuer-based fetch fails
5. **Accept token's own issuer** if it's a valid Azure CIAM issuer

### Key Changes

**File**: `backend/api/middleware/auth.py`

#### 1. Updated `get_jwks()` method
- Now accepts optional `issuer` parameter
- Derives JWKS endpoint from issuer: `{issuer}/discovery/v2.0/keys`
- Falls back to configured endpoint if issuer-based fetch fails

#### 2. Updated `validate_token()` method
- **First step**: Decode token without verification to get issuer
- **Second step**: Fetch JWKS from token's issuer (not pre-configured endpoint)
- **Third step**: Validate signature, audience, and issuer
- **Enhanced logging**: Logs token claims, issuer, and validation steps

## How It Works Now

```
1. Token arrives at backend
   ↓
2. Decode token (unverified) → Extract issuer: https://{GUID}.ciamlogin.com/{GUID}/v2.0
   ↓
3. Derive JWKS endpoint: https://{GUID}.ciamlogin.com/{GUID}/discovery/v2.0/keys
   ↓
4. Fetch JWKS from token's issuer
   ↓
5. Find signing key (KID) in JWKS
   ↓
6. Validate token signature, audience, issuer
   ↓
7. Return SecurityContext
```

## Testing

### Diagnostic Script

Use the comprehensive diagnostic script to test token validation:

```bash
# Get a token from your browser after logging in
# (Check DevTools > Application > Local Storage for MSAL tokens)

# Run diagnostic
AUTH_TOKEN='your-token-here' python3 scripts/diagnose-auth-token.py
```

The script will:
- Decode and display token claims (issuer, audience, tenant ID, etc.)
- Test multiple JWKS endpoints
- Validate token using the auth middleware
- Provide specific error messages and fixes

### Manual Testing

1. **Login via Google** in the frontend
2. **Get token** from browser DevTools:
   - Open DevTools (F12)
   - Go to Application > Local Storage
   - Look for MSAL tokens or check Network tab for Authorization header
3. **Test API endpoint**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://your-api-url/api/v1/chat \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"content": "test"}'
   ```

## Configuration

Ensure these environment variables are set:

```env
AZURE_AD_TENANT_ID=6684288a-b805-4161-bf41-ba2121e51c90  # or engramai.onmicrosoft.com
AZURE_AD_CLIENT_ID=e32c6c40-...  # Your app registration client ID
AZURE_AD_EXTERNAL_ID=true
AZURE_AD_EXTERNAL_DOMAIN=engramai
AUTH_REQUIRED=true  # Set to false for POC/development
```

## Enhanced Logging

The middleware now logs:
- Token claims (issuer, audience, tenant ID) on validation
- JWKS endpoint being used
- Successful token validation with user ID
- Specific error messages for issuer/audience mismatches

Check logs with:
```bash
az containerapp logs show \
  --name staging-env-api \
  --resource-group engram-rg \
  --tail 100 \
  --type console | grep -iE "(token|auth|issuer|jwks)"
```

## Common Issues

### Issue: "Invalid token signature - signing key not found"

**Cause**: JWKS endpoint doesn't have the key for the token's KID

**Fix**: The new code automatically fetches JWKS from the token's issuer, which should resolve this.

### Issue: "Invalid token audience"

**Cause**: Token audience doesn't match expected client ID

**Check**:
- Frontend is requesting correct scope: `api://{CLIENT_ID}/user_impersonation`
- Backend `AZURE_AD_CLIENT_ID` matches frontend client ID
- Token audience is either `{CLIENT_ID}` or `api://{CLIENT_ID}`

### Issue: "Invalid token issuer"

**Cause**: Token issuer not in allowed list

**Fix**: The new code automatically accepts the token's issuer if it's a valid Azure CIAM issuer.

## Verification

After deploying the fix:

1. ✅ Users can login with Google
2. ✅ Chat API accepts authenticated requests
3. ✅ Voice API accepts authenticated requests  
4. ✅ Episodes/Memory API accepts authenticated requests
5. ✅ Stories API accepts authenticated requests

## Files Modified

- `backend/api/middleware/auth.py` - Updated token validation logic
- `scripts/diagnose-auth-token.py` - New diagnostic tool

## Related Documentation

- [Authentication Architecture Analysis](../architecture/authentication-analysis.md)
- [Entra External ID Setup](../architecture/entra-external-id.md)
- [Troubleshooting Guide](./chat-voice-episodes-401-errors.md)

