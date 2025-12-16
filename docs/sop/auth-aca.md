# AuthN/AuthZ SOP - Azure Container Apps

## Identity
- Assign user-assigned MI to each app; set `AZURE_CLIENT_ID` env for MI usage in code.
- Use secret references from Key Vault; avoid embedding secrets in env values.

## Ingress
- Backend: external HTTPS with cert; consider WAF/APIM for prod; CORS restricted per env.
- Zep/Temporal server: internal-only.
- UI (Temporal) if exposed: auth protect and restrict by IP.

## Secrets
- Managed via Key Vault references (Postgres password break-glass, Zep API key, Azure AI key for non-prod).

## Logging
- Send ACA logs to Log Analytics; enable app logs; monitor auth failures.

## Scaling
- Scale rules should not bypass auth; keep min replicas for warm start where needed.
# SOP: Azure Container Apps
- Identity: user-assigned MI per app; set `AZURE_CLIENT_ID` where needed; reference secrets from Key Vault.
- Ingress: backend external; worker/zep/temporal-server internal only; disable `allowInsecure`.
- Secrets: use `keyVaultUrl` with MI; avoid inline secrets.
- Scaling: keep minReplicas>0 for auth-critical services to avoid token fetch latency.
- Network: consider VNet integration + internal environment for higher envs.
- Logging: enable diagnostics to Log Analytics; monitor auth failures.
# Auth SOP – Azure Container Apps

## Identity
- Assign user-assigned MI to each app (backend, worker, zep, temporal-server/ui as needed).
- Set `AZURE_CLIENT_ID` env when MI used for downstream services.

## Secrets
- Use Key Vault secret refs for DB pwd, Zep key, any legacy keys.
- Prefer MI auth for Azure AI, Storage, Postgres (AAD).

## Ingress
- Backend: external with HTTPS; consider APIM/WAF in prod.
- Internal-only for Zep/Temporal server; worker no ingress.
- CORS restricted per env; no `*` in prod.

## Logging
- Enable diagnostics to Log Analytics; monitor auth failures and MI token issues.
# SOP: Azure Container Apps

## Identity
- Assign User-Assigned MI to apps; pass `AZURE_CLIENT_ID` env.
- Pull secrets via KV references using the same MI.

## Ingress
- Backend: external HTTPS; consider APIM/WAF for prod.
- Zep/Temporal server: internal-only.
- UI (Temporal): external only when auth enabled.

## Config
- No inline secrets; all from KV.
- CORS restricted per env; no wildcard in prod.

## Monitoring
- App logs to Log Analytics; alert on 401/403 spikes and secret retrieval failures.

