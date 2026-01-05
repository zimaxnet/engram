---
layout: default
title: "Entra External ID Authentication"
parent: "Architecture"
---

# Entra External ID Authentication

## Overview

Engram uses **Microsoft Entra External ID** (CIAM) for user authentication, enabling:

- Google social login
- Self-service sign-up
- Secure JWT-based API access

## Configuration

### Tenant Details

| Property | Value |
|----------|-------|
| Tenant Domain | `engramai.onmicrosoft.com` |
| Authority | `https://engramai.ciamlogin.com/engramai.onmicrosoft.com` |
| App Registration | `engram-frontend` |
| Client ID | `94d50189-d4de-4b80-8804-2f3bf2e2d14f` |

### Identity Providers

- **Google** - OAuth 2.0 social login

### User Flow

- **Name**: SignUpSignIn
- **Type**: Sign up and sign in
- **Providers**: Google
- **Attributes**: Email, Display Name

## Architecture

```
┌─────────────────┐     ┌─────────────────────────┐
│                 │     │  Entra External ID      │
│   Frontend      │────▶│  engramai.ciamlogin.com │
│   (MSAL.js)     │     │                         │
│                 │◀────│  ┌─────────────────┐   │
└────────┬────────┘     │  │  Google OAuth   │   │
         │              │  └─────────────────┘   │
         │              └─────────────────────────┘
         │ JWT Token
         ▼
┌─────────────────┐
│    Backend      │
│  api.engram.work│
│                 │
│  JWT Validation │
│  (auth.py)      │
└─────────────────┘
```

## Frontend Integration

### Files

- `frontend/src/auth/authConfig.ts` - MSAL configuration
- `frontend/src/auth/AuthContext.tsx` - React context for auth state
- `frontend/src/auth/index.ts` - Barrel exports
- `frontend/src/main.tsx` - MsalProvider wrapper

### Environment Variables

```env
VITE_AZURE_AD_TENANT_DOMAIN=engramai
VITE_AZURE_AD_TENANT_ID=engramai.onmicrosoft.com
VITE_AZURE_AD_CLIENT_ID=94d50189-d4de-4b80-8804-2f3bf2e2d14f
VITE_REDIRECT_URI=https://engram.work
```

### Usage

```tsx
import { useAuth } from './auth';

function LoginButton() {
  const { isAuthenticated, login, logout, user } = useAuth();
  
  if (isAuthenticated) {
    return (
      <div>
        <span>Welcome, {user?.name}</span>
        <button onClick={logout}>Sign Out</button>
      </div>
    );
  }
  
  return <button onClick={login}>Sign in with Google</button>;
}
```

## Backend Integration

### Environment Variables

```env
AZURE_AD_TENANT_ID=engramai.onmicrosoft.com
AZURE_AD_CLIENT_ID=94d50189-d4de-4b80-8804-2f3bf2e2d14f
AZURE_AD_EXTERNAL_ID=true
AZURE_AD_EXTERNAL_DOMAIN=engramai
AUTH_REQUIRED=false  # Set to true when ready for production
```

### JWT Validation

The backend validates JWTs from Entra External ID using:

- **JWKS Endpoint**: `https://engramai.ciamlogin.com/engramai.onmicrosoft.com/discovery/v2.0/keys`
- **Issuer**: `https://engramai.ciamlogin.com/engramai.onmicrosoft.com/v2.0`
- **Audience**: Frontend Client ID

### Files

- `backend/api/middleware/auth.py` - EntraIDAuth class with External ID support

## Secrets Management

### GitHub Actions Secrets

| Secret | Description |
|--------|-------------|
| `AZURE_AD_TENANT_ID` | engramai.onmicrosoft.com |
| `AZURE_AD_CLIENT_ID` | Frontend app client ID |
| `AZURE_AD_EXTERNAL_ID` | true |
| `AZURE_AD_EXTERNAL_DOMAIN` | engramai |

### Azure Key Vault

| Secret | Description |
|--------|-------------|
| `azure-ad-client-id` | Frontend app client ID |
| `azure-ad-tenant-id` | Tenant ID |

## Google OAuth Setup

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Set redirect URI: `https://engramai.ciamlogin.com/engramai.onmicrosoft.com/oauth2/authresp`
3. Add Client ID and Secret to Entra External ID → Identity providers → Google

## Troubleshooting

### Common Issues

1. **CORS errors**: Ensure redirect URIs match exactly
2. **Token validation fails**: Check issuer/audience match
3. **Google login not appearing**: Verify user flow has Google enabled
4. **401 after deployment**: Check `AUTH_REQUIRED` setting and that External ID env vars are set

### Debug Logging

Enable MSAL verbose logging in development:

```ts
// authConfig.ts
logLevel: import.meta.env.DEV ? LogLevel.Verbose : LogLevel.Error,
```

## Security Notes

- Tokens are stored in `localStorage` (configurable to `sessionStorage`)
- ID tokens contain user profile claims
- Access tokens are used for API calls
- Refresh tokens enable silent token renewal
