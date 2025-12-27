# SOP: Azure SWA + Container Apps Authentication

> **TL;DR**: When API calls return 401 Unauthorized, check both the SWA config AND the Container App authConfig. Both layers can block requests independently.

## Problem Summary

Azure Static Web Apps (SWA) with a linked Container Apps backend has **two authentication layers** that can independently block API requests:

1. **SWA Layer** (`staticwebapp.config.json`) - Routes and roles
2. **Container App Layer** (`authConfig` resource in Bicep) - Platform-level auth

Even if one layer allows anonymous access, the other can still enforce authentication.

---

## Common Symptoms

| Symptom | Likely Cause |
|---------|--------------|
| 401 on all `/api/*` routes | SWA config missing `anonymous` role OR Container App AAD enabled |
| 401 with valid SWA config | Container App `authConfig` has AAD `identityProviders` enabled |
| Timeout on API calls | Container App not running (check revision status) |
| Internal health checks pass, external 401 | Platform auth on Container App |

---

## Configuration Files

### 1. SWA Config (`frontend/staticwebapp.config.json`)

```json
{
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["anonymous", "authenticated"]
    },
    {
      "route": "/*",
      "allowedRoles": ["anonymous", "authenticated"]
    }
  ]
}
```

> [!WARNING]
> **Do NOT include incomplete AAD settings with placeholders like `<TENANT_ID>`.**
> This breaks the config silently and may cause 401s.

### 2. Container App Auth (`infra/modules/backend-aca.bicep`)

For **staging/POC** (auth disabled at platform level):

```bicep
resource authConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = {
  parent: backendApp
  name: 'current'
  properties: {
    platform: {
      enabled: false  // Auth handled by application code
    }
    globalValidation: {
      unauthenticatedClientAction: 'AllowAnonymous'
    }
    // NO identityProviders block for staging
  }
}
```

For **production** (proper AAD auth):

```bicep
resource authConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = {
  parent: backendApp
  name: 'current'
  properties: {
    platform: {
      enabled: true  // Platform enforces auth
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: '<REGISTERED_APP_CLIENT_ID>'
          openIdIssuer: 'https://login.microsoftonline.com/<TENANT_ID>/v2.0'
        }
        validation: {
          allowedAudiences: ['api://<APP_NAME>']
        }
      }
    }
  }
}
```

---

## Debugging Checklist

When you see 401 Unauthorized:

- [ ] **Check SWA config** has `"allowedRoles": ["anonymous"]` for `/api/*`
- [ ] **Check Container App authConfig** has `platform.enabled: false` for staging
- [ ] **Verify no AAD identityProviders** in authConfig (staging only)
- [ ] **Check container logs** to see if requests reach the app
- [ ] **Test internal vs external** — internal health checks pass but external fails = platform auth

### Useful Commands

```bash
# Check Container App status
az containerapp show --name "staging-env-api" --resource-group "engram-rg" \
  --query "{state:properties.runningStatus,revision:properties.latestRevisionName}"

# View container logs (last 20 lines)
az containerapp logs show --name "staging-env-api" --resource-group "engram-rg" \
  --type console --tail 20

# Test API directly (bypasses SWA)
curl "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/health"

# Test through SWA
curl "https://engram.work/api/v1/agents"
```

---

## Environment-Based Auth Strategy

| Environment | Platform Auth | Application Auth | Notes |
|-------------|---------------|------------------|-------|
| Local/Dev | Off | Off (`AUTH_REQUIRED=false`) | Fastest iteration |
| Staging/POC | Off | Off | Validate system works |
| UAT | On | Optional | Test auth flow |
| Production | On | On | Full security |

---

## References

- [Azure SWA Authentication](https://learn.microsoft.com/en-us/azure/static-web-apps/authentication-authorization)
- [Container Apps Auth Config](https://learn.microsoft.com/en-us/azure/container-apps/authentication)
- See also: `docs/sop/auth-environments-nist-ai-rmf.md`
