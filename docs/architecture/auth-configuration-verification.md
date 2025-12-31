# Authentication Configuration Verification

## Overview

This document verifies that the authentication configuration correctly handles:
1. Token audience format (`api://{CLIENT_ID}` vs `{CLIENT_ID}`)
2. Token issuer format (GUID-based vs named-domain)

---

## Token Audience Configuration

### Frontend Configuration

**File**: `frontend/src/auth/authConfig.ts`

```typescript
// API scopes for backend authentication
export const apiRequest = {
    scopes: CLIENT_ID ? [`api://${CLIENT_ID}/user_impersonation`] : ['openid', 'profile', 'email'],
};
```

**Result**: Frontend requests scope `api://{CLIENT_ID}/user_impersonation`

### Backend Configuration

**File**: `backend/api/middleware/auth.py`

```python
# Validate audience
# When requesting scope api://{CLIENT_ID}/user_impersonation, the token audience
# will be api://{CLIENT_ID}, not just the CLIENT_ID
# Accept both formats for flexibility
valid_audiences = []
if self.client_id:
    # Client ID itself (for .default scope tokens)
    valid_audiences.append(self.client_id)
    # App ID URI format (for api://{CLIENT_ID}/user_impersonation scope tokens)
    valid_audiences.append(f"api://{self.client_id}")
```

**Result**: Backend accepts both:
- `{CLIENT_ID}` (for `.default` scope tokens)
- `api://{CLIENT_ID}` (for `api://{CLIENT_ID}/user_impersonation` scope tokens)

### Verification

✅ **Configuration is correct**

- Frontend requests: `api://{CLIENT_ID}/user_impersonation`
- Azure CIAM returns token with audience: `api://{CLIENT_ID}`
- Backend accepts: `api://{CLIENT_ID}` ✅

**No mismatch** - The backend correctly accepts the `api://{CLIENT_ID}` format that Azure CIAM returns when the frontend requests `api://{CLIENT_ID}/user_impersonation` scope.

---

## Token Issuer Configuration

### Azure CIAM Behavior

Azure CIAM issues tokens with GUID-based issuers:
```
https://{GUID}.ciamlogin.com/{GUID}/v2.0
```

Even when the authority URL uses a named domain:
```
https://engramai.ciamlogin.com/{tenant_id}
```

### Backend Configuration

**File**: `backend/api/middleware/auth.py`

#### Previous Approach (Failed)
```python
# Fetched JWKS from configured endpoint
jwks = await self.get_jwks()  # Uses configured jwks_uri
# Problem: JWKS from wrong endpoint, signing key not found
```

#### Current Approach (Fixed)
```python
# 1. Decode token (unverified) to extract issuer
unverified_payload = jwt.decode(token, options={"verify_signature": False})
token_issuer = unverified_payload.get("iss")

# 2. Fetch JWKS from token's issuer (standard JWT validation)
jwks = await self.get_jwks(issuer=token_issuer)
# Derives: {token_issuer}/discovery/v2.0/keys

# 3. Validate token with correct signing keys
```

### Verification

✅ **Configuration is correct**

- Token issuer: `https://{GUID}.ciamlogin.com/{GUID}/v2.0`
- JWKS fetched from: `https://{GUID}.ciamlogin.com/{GUID}/discovery/v2.0/keys`
- Signing key found: ✅
- Token validation succeeds: ✅

**No mismatch** - The backend now fetches JWKS from the token's actual issuer, regardless of whether it's GUID-based or named-domain.

---

## Configuration Matrix

| Component | Configuration | Token Format | Status |
|-----------|--------------|--------------|--------|
| **Frontend Scope** | `api://{CLIENT_ID}/user_impersonation` | N/A | ✅ Correct |
| **Token Audience** | `api://{CLIENT_ID}` | From Azure CIAM | ✅ Accepted |
| **Backend Audience Check** | Accepts both `{CLIENT_ID}` and `api://{CLIENT_ID}` | Validation | ✅ Correct |
| **Token Issuer** | `https://{GUID}.ciamlogin.com/{GUID}/v2.0` | From Azure CIAM | ✅ Handled |
| **JWKS Endpoint** | Derived from token's issuer | Dynamic | ✅ Correct |
| **Backend Issuer Check** | Accepts token's own issuer if valid Azure CIAM | Validation | ✅ Correct |

---

## Testing Checklist

### Audience Testing

- [x] Frontend requests `api://{CLIENT_ID}/user_impersonation` scope
- [x] Backend accepts `api://{CLIENT_ID}` audience
- [x] Backend accepts `{CLIENT_ID}` audience (fallback)
- [x] Error handling for invalid audience

### Issuer Testing

- [x] Backend fetches JWKS from token's issuer
- [x] Backend handles GUID-based issuers
- [x] Backend handles named-domain issuers
- [x] Fallback to configured endpoint if issuer-based fetch fails
- [x] Error handling for invalid issuer

### Integration Testing

- [x] Google login → Token issued
- [x] Token sent to backend → JWKS fetched from correct endpoint
- [x] Token validated → User authenticated
- [x] API requests succeed → Chat, Voice, Episodes, Stories work

---

## Diagnostic Tools

### Token Inspection

```bash
AUTH_TOKEN='your-token' python3 scripts/diagnose-auth-token.py
```

**Checks:**
- Token audience format
- Token issuer format
- JWKS endpoint accessibility
- Token validation

### Logging

Backend logs include:
- Token claims (issuer, audience, tenant ID)
- JWKS endpoint being used
- Validation success/failure
- Specific error messages

---

## Conclusion

✅ **All configurations are correct**

1. **Audience**: Frontend requests `api://{CLIENT_ID}/user_impersonation`, backend accepts `api://{CLIENT_ID}` ✅
2. **Issuer**: Backend fetches JWKS from token's issuer (GUID or named-domain) ✅
3. **Validation**: Token validation succeeds with correct signing keys ✅

The authentication flow is properly configured to handle Azure CIAM's token formats.

---

**Last Verified**: 2025-01-XX  
**Status**: ✅ All configurations verified and correct

