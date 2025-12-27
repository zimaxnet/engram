# AuthN/AuthZ SOP - FastAPI / FastMCP

## Goals
- Strong, consistent Entra-based auth for higher environments.
- Low-friction toggle for POC validation, with an explicit switch to re-enable strong auth.
- Avoid identity variable collisions between **Entra app registration** and **Managed Identity**.

## Authentication (AuthN)
- **User requests**: Entra bearer tokens (`Authorization: Bearer <token>`).
- **Issuer**: tenant v2 endpoint (`https://login.microsoftonline.com/<tenant>/v2.0`).
- **Audience**: the API app registration client ID (or App ID URI), depending on your token configuration.

### Environment variables (important)
- **`AZURE_AD_CLIENT_ID`**: Entra **app registration** client ID used by the API for JWT audience validation.
- **`AZURE_TENANT_ID`**: Entra tenant ID (also used by some Azure SDK auth flows).
- **`AZURE_CLIENT_ID`**: user-assigned **Managed Identity** client ID for Azure SDKs (DefaultAzureCredential).  
  Do **not** reuse this for the Entra app registration client ID.
- **`AUTH_REQUIRED`**: `true|false`. When `false`, the API bypasses auth (POC only).

### POC / low-friction mode (for validation only)
- Set `AUTH_REQUIRED=false` on the API container app (and any components that require user auth).
- Disable any **platform/edge auth** configured on the hosting layer (e.g., Container App Authentication) so requests reach FastAPI.
- Re-enable `AUTH_REQUIRED=true` before moving to UAT/Prod.

### Smoke-test prerequisites (token-based)
- Expose a scope on the API (e.g., `user_impersonation`).
- Authorize the Azure CLI client app (`04b07795-8ddb-461a-bbee-02f9e1bf7b46`) as an authorized client for that scope.
- Fetch token with explicit scope (avoid `.default` when troubleshooting):
  `az account get-access-token --scope "api://<APP_ID_URI>/user_impersonation" --query accessToken -o tsv`

## Authorization (AuthZ)
- Map Entra app roles → internal roles (Admin, Analyst, PM, Viewer).
- Enforce via FastAPI dependencies (`require_roles`, `require_scopes`) and keep `/health` unauthenticated.

## MCP
- Mounted at `/api/v1/mcp`; reuse the same auth dependency as the REST API.
- Rate-limit at ingress/WAF when publicly exposed.

## CORS
- Dev/Test: include localhost ports.
- Staging/UAT: restrict to env frontends.
- Prod: no wildcards.

## Secrets & Config
- Prefer Managed Identity for Azure resources; keep API keys out of code.
- If Key Vault overlay is used, ensure Managed Identity selection is not broken by misusing `AZURE_CLIENT_ID`.

## Logging
- Log auth failures with minimal PII; include correlation IDs; alert on 401/403 spikes.

