# Engram AuthN/AuthZ Master SOP

## Scope
- Environments: dev, test, uat, staging, prod.
- Components: Entra ID, FastAPI/FastMCP, Container Apps/AKS, Postgres, Key Vault, Storage, Zep, Temporal, SWA, CI/CD.

## Roles (App + Platform)
- App roles: Admin (full), Analyst (chat/memory/agents), PM (workflows/agents), Viewer (read).
- Platform roles: SRE/Ops (deployment + monitoring), Security (policy/CA), DBA (Postgres admin), Dev (non-prod deploy).

## Identity Principles
- Single identity: Entra ID for users; Managed Identities (MI) for workloads.
- Least privilege + RBAC everywhere; no shared secrets; keys only for break-glass in lower envs.
- Network-first: private ingress for internal services; WAF/APIM for public surfaces.
- Secrets in Key Vault; prefer MI to fetch; rotate on schedule and on incident.

## Token & Audience
- Audience/App ID URI per env: `api://engram-<env>`.
- Issuer: tenant-specific `https://login.microsoftonline.com/<tenant>/v2.0`.
- Scopes: `user_impersonation` + app roles.

## Environment Matrix (policy by default)
- Dev/Test: MI preferred, keys allowed; dev tokens allowed; open CORS for localhost; Temporal/Zep internal only.
- UAT/Staging: MI required; no dev tokens; CORS limited to env frontends; Zep/Temporal internal; API protected by Entra.
- Prod: MI only; WAF/APIM; strict CORS; private backplanes; no public DB/storage; Temporal with mTLS; Zep internal-only.

## Incident Response (Auth-related)
1) Contain: revoke user/SP, disable MI role assignments if compromised, rotate secrets.  
2) Eradicate: rotate keys, purge tokens (revoke sessions), redeploy containers.  
3) Recover: validate access, re-enable least-privilege, run smoke tests.  
4) Review: log review (KV, Postgres, Storage, API), RCA, tighten policies.

## Logging & Monitoring
- Enable diagnostics to Log Analytics for API, Container Apps/AKS, Key Vault, Storage, Postgres, Temporal, Zep ingress (if available).
- Alerts: auth failures surge, RBAC assignment changes, KV secret get/list spikes.

## Change Control
- All auth config via Bicep/manifests; no ad-hoc portal changes in prod.
- PR + review + environment-specific approvals; CI/CD with OIDC.
# Engram AuthN/AuthZ Master SOP

## Scope
- Applies to all environments: dev, test, uat, staging, prod.
- Covers FastAPI/FastMCP, workers, Temporal, Zep, Postgres, Storage, Key Vault, SWA, CI/CD, Azure AI, AKS/ACA.

## Identity Principles
- Azure Entra ID as single identity plane for users; Managed Identity (MI) for workloads.
- Least privilege via RBAC (Entra roles, Azure RBAC, service-level roles).
- Secrets in Key Vault only; prefer MI over keys; rotate keys when MI unavailable.
- Network before identity where possible (private endpoints, WAF/APIM, internal ingress).
- Strong transport: HTTPS/TLS everywhere; mTLS where supported (Temporal prod); HSTS on public endpoints.

## Roles (App / Entra App Roles)
- Admin: full platform + data admin.
- Analyst: chat/memory/agents.
- PM: workflows/agents.
- Viewer: read-only.

## Environment Matrix (Auth Expectations)
- Dev/Test: Entra tokens preferred; dev token fallback allowed; MI optional.
- UAT/Staging: Entra required; MI required; no dev tokens; keys only as break-glass.
- Prod: Entra only; MI only; no dev tokens; WAF/APIM front door; private backplane.

## Token & Audience
- Audience: env-specific App ID URI (e.g., `api://engram-staging`, `api://engram-prod`).
- Issuer: tenant-specific (`https://login.microsoftonline.com/<tenant>/v2.0`).
- Scopes: `user_impersonation`; roles mapped to internal RBAC.

## Workload Identity
- Container Apps: user-assigned MI per service (backend, worker, temporal, zep if needed).
- AKS: workload identity with federated service accounts; set `AZURE_CLIENT_ID` where required.
- Assign minimal Azure roles: KV Secrets User, Storage Blob Data Reader/Contributor, Cognitive Services OpenAI User, Postgres AAD roles.

## Secrets & Key Management
- Store all secrets in Key Vault; reference via secret refs in ACA/AKS.
- Enable soft-delete + purge protection (prod); logging enabled.
- Rotation: keys/tokens every 90 days; Zep API keys every 60 days; break-glass creds 24h max.

## Network Controls
- Private endpoints for Postgres, Storage, Key Vault in uat/prod.
- Internal ingress for Zep/Temporal server; Temporal UI gated; API public via WAF/APIM in prod.
- CORS restricted to env origins (SWA/portal); no wildcard in prod.
- Network policies in AKS: default deny; allow explicit paths API→Zep, Worker→Temporal, API→Postgres.

## Audit & Logging
- Enable diagnostic logs: Container Apps/AKS, API, Key Vault, Storage, Postgres, Temporal, Zep ingress.
- Centralize in Log Analytics + App Insights; retain per env (prod ≥365d).
- Alert on auth failures, RBAC changes, secret access anomalies.

## Credential Lifecycle SOP
1. Provision: create Entra app per env; define roles; register redirect URIs; expose API scope.
2. Assign: map Entra groups to app roles; assign MI to resources with least privilege.
3. Distribute: never share secrets directly; use KV references; for CI/CD use OIDC federation (no static creds).
4. Rotate: schedule rotations; update KV; restart workloads after rotation; verify health.
5. Revoke: disable principal or remove role assignment; rotate impacted secrets; invalidate tokens by app role removal.

## Incident Response (AuthN/AuthZ)
1. Contain: revoke app role assignments; disable compromised identities; remove MI role bindings.
2. Eradicate: rotate secrets/keys; redeploy workloads; rotate Zep API key; reset Postgres creds.
3. Recover: validate health/readiness; re-enable access gradually by role; monitor logs for anomalies.
4. Lessons: post-incident review; tighten RBAC/CORS/ingress; update runbooks.

## Validation Checklist (per release)
- API: `/health`, `/ready` with valid bearer token; role-based access tests.
- MCP: SSE endpoint accepts Entra token; rejects anonymous.
- Postgres: MI-based connection succeeds; password auth disabled in prod.
- Storage: MI read/write as scoped; no public containers.
- Zep: API key required; network internal-only.
- Temporal: UI gated; server internal; mTLS/OIDC in prod.
- SWA: Entra login enforced; routes protected.
- CI/CD: OIDC login only; no PAT/secret in repo; principle scoped to RG/subset.
# Engram AuthN/AuthZ SOP (All Environments)

## Scope
- Applies to dev, test, uat, staging (ACA) and prod (AKS) for all components: FastAPI, FastMCP, SWA, Zep, Temporal, PostgreSQL, Storage, Key Vault, Azure AI/VoiceLive, CI/CD.

## Principles
- Entra ID as single identity plane; Managed Identity (MI) for workloads.
- Least privilege RBAC; network first (private ingress where possible).
- Secrets in Key Vault; prefer MI over keys; short-lived tokens.
- Environment isolation: separate app registrations and resource instances per env.
- Audit everything: App/Entra sign-ins, KV access, Postgres, Storage, ACA/AKS diagnostics.

## Roles
- App roles: Admin, Analyst, PM, Viewer (mapped from Entra app roles).
- Azure RBAC: scope MIs narrowly (Key Vault Secrets User, Storage Blob Data Contributor, Cognitive Services OpenAI User, Monitoring Reader).
- DB roles: app_rw, analytics_ro, admin.
- Temporal roles: admin, worker, viewer.

## Token & Credential Policy
- Prod: MI only for services; no dev tokens; enforce TLS.
- Lower env: dev tokens allowed for debugging; keys allowed but rotate every 30 days.
- CI/CD: OIDC federation only (no stored client secrets).

## Network Policy
- Prod: private endpoints for KV/Storage/Postgres; AKS private cluster; WAF/APIM for public API; Temporal/Zep internal-only.
- Lower env: public allowed only where necessary; restrict admin surfaces by IP allowlists.

## Incident Response
- Revoke access: disable user, remove role assignments, rotate keys/secrets, recycle pods/containers.
- Investigate: review Entra sign-ins, KV access logs, Postgres audit, Storage logs, ACA/AKS diagnostics.
- Restore: re-issue tokens/roles with least privilege; document timeline.

## Validation
- Per release: token validation (aud/iss), MI flow to KV/Storage/Postgres, API role enforcement, Temporal access control, Zep key check, SWA auth.

# Engram AuthN/AuthZ SOP (All Environments)

## Scope
- Applies to dev, test, uat, staging, prod.
- Components: FastAPI, FastMCP, Zep, Temporal, Postgres, Storage, Key Vault, Container Apps/AKS, SWA, Azure AI, CI/CD.

## Principles
- Entra ID as single identity plane; Managed Identity (MI) for workloads.
- Least privilege, RBAC everywhere; private networking first.
- Secrets only in Key Vault; prefer MI over keys.
- Separate Entra apps and resources per environment.
- Audit and log all auth events; rotate secrets per policy; incident playbooks below.

## Roles (App / Platform)
- App roles: Admin (full), Analyst (chat/memory), PM (workflows/agents), Viewer (read-only).
- Platform roles: SRE/Ops (deploy/infra), Security (audit), DBA (Postgres), Data (read-only analytics).

## Token & Audience
- Audience: environment-specific App ID URI (api://engram-<env>).
- Issuer: tenant login.microsoftonline.com/<tenant>.
- Scopes: user_impersonation + app roles.

## Network Controls
- Prod/UAT: private endpoints for KV/Storage/Postgres; WAF/APIM in front of public API; Temporal/Zep internal only.
- Dev/Test/Staging: ACA with restricted ingress; allow localhost CORS only where needed.

## Credential Lifecycle
- MI preferred; keys only for lower env break-glass.
- Store all secrets in Key Vault; never in repo.
- Rotate keys/secrets quarterly or on incident; revoke MI role assignments if compromised.

## Incident Response
- Revoke access: disable user/service principal; remove MI role assignments.
- Rotate: KV secrets, storage keys (if used), Postgres passwords, Zep API keys.
- Audit: review Entra sign-ins, KV access logs, Container Apps/AKS logs, Postgres audit, storage access logs.
- Contain: tighten NSGs/private endpoints; disable public ingress if needed.

## Environment Matrix (Auth Expectations)
- Dev/Test: Entra auth required; dev tokens allowed for local; MI preferred; keys allowed.
- UAT/Staging: Entra required; MI required; keys only break-glass; CORS limited to env fronts.
- Prod: Entra required; MI only; no dev tokens; WAF/APIM; private data planes; Temporal/Zep internal; SWA Entra auth.


