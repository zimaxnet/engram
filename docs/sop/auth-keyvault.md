# AuthN/AuthZ SOP - Key Vault

## Access Model
- RBAC enabled; no access policies.
- Roles: `Key Vault Secrets User` for app MIs; `Key Vault Administrator` only for platform ops; `Key Vault Reader` for monitoring tools.

## Network
- Prod/UAT: private endpoints; disable public network. Staging: allow public if needed; prefer private when possible.

## Secrets
- Store: Postgres password (break-glass), Zep API key, Azure AI key (non-prod only), registry password, CI/CD client secret (if any).
- Use secret references in Container Apps/AKS; never write secrets to env vars in code.

## Rotation
- Keys/secrets rotation at 90d prod, 180d non-prod; Zep/registry keys 90d.
- Update references and restart apps after rotation.

## Auditing
- Enable diagnostic logs to Log Analytics; alert on secret get/list spikes and on new role assignments.
# SOP: Key Vault
- RBAC-only access; disable access policies.
- Enable soft-delete and purge protection in prod; enable logging to Log Analytics.
- Access:
  - Workloads via user-assigned MI (`Key Vault Secrets User` role).
  - CI/CD via OIDC-federated SP with scoped access.
- Secrets: store all API keys, DB passwords (non-prod), Zep keys; no secrets in code/repo.
- Network: private endpoints for uat/prod; public allowed only in lower envs.
- Rotation: 90d cadence; break-glass secrets 24h max; document rotation in change log.

# Auth SOP – Key Vault

## Access
- Use RBAC, not access policies. Roles: Key Vault Secrets User for apps; Key Vault Administrator for platform ops only.
- Assign MI of backend/worker/aks workloads to Secrets User.

## Network
- Prod: private endpoint; disable public network.
- Lower env: public OK; still require RBAC.

## Operations
- Enable soft delete + purge protection (prod); log to Log Analytics.
- Store all secrets (DB, Zep, any keys) here; reference via KeyVault URLs in ACA/AKS.
- Rotation: 90 days or per policy; update KV reference only (no code changes).
# SOP: Key Vault

## AuthN/Z
- RBAC mode enabled. Roles: Key Vault Secrets User for apps (MI), Key Vault Administrator for platform-only.
- No access policies unless required.

## Hardening
- Soft delete + purge protection in prod; enable private endpoint for prod/uat.
- Disable public access where possible; restrict to trusted networks.

## Usage
- Secrets only; no app settings stored in code.
- Use UAMI to pull secrets via Container Apps/AKS with `AZURE_CLIENT_ID`.

## Rotation & Audit
- Rotate secrets per policy; record owners.
- Enable diagnostic logs to Log Analytics; alert on purge/delete events.

