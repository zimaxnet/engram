# AuthN/AuthZ SOP - PostgreSQL

## Authentication
- Enable AAD authentication on Flexible Server.
- Set AAD admin (ops group) per env.
- Backend/worker identities map to DB roles; avoid password auth in prod.

## Roles
- `engram_app_rw` for backend/worker MI (schema owner for app tables).
- `engram_readonly` for analytics.
- `engram_admin` for DBAs (minimal membership).

## Network
- Private endpoints in uat/prod; disable public network; TLS required.
- Non-prod may allow public for speed, but prefer VNet + firewall rules.

## Secrets
- Connection strings only for dev/test; in higher env use AAD auth string with `Authentication=ActiveDirectoryMsi;` and `ClientId` if user-assigned.
- Store any break-glass passwords in Key Vault; rotate 90d (non-prod 180d).

## Hardening
- Enforce `ssl_min_protocol_version=TLS1.2`; `log_connections`, `log_disconnections`.
- Periodic role review; drop unused logins; audit extensions.

## Migration/Seed
- Run migrations via MI; do not use superuser in pipelines.
# SOP: PostgreSQL
- AuthN: Enable AAD authentication (flexible server) for uat/staging/prod; keep password only in dev/test.
- AAD Admin: assign platform admin group; disallow individual user sprawl.
- Roles:
  - `app_rw` for backend/worker MI.
  - `analytics_ro` for reporting.
  - `admin` limited to DBAs.
- Connection: MI with `ENCLAVE` TLS; disable public access in prod; use private endpoint.
- Rotation: rotate passwords every 90d where still used; prefer MI to remove passwords.
- Auditing: enable server logs; forward to Log Analytics; alert on failed logins.

# Auth SOP – PostgreSQL

## AuthN
- Prefer AAD integration (flex server): enable `activeDirectoryAuth`.
- Set AAD admin (ops group); disable password login in prod once MI mapped.
- Lower env: password allowed; rotate every 30 days.

## Roles
- `app_rw` for backend/worker MI; `analytics_ro` for reporting; `admin` for DBA only.
- Grant schema privileges: SELECT/INSERT/UPDATE/DELETE on app schema; no superuser.

## Network
- Prod: private endpoint; deny public network.
- Lower env: allow AzureServices; restrict by firewall rules.

## Rotation & Auditing
- Rotate admin pwd via KV secret; enable log to Log Analytics; review audit quarterly.
# SOP: PostgreSQL

## AuthN
- Enable AAD authentication (Flexible Server authConfig: activeDirectoryAuth=Enabled).
- Set AAD admin (security group); MI access for backend/worker.
- Password auth only for lower env or break-glass; store in Key Vault.

## Roles
- DB roles: app_rw (backend/worker MI), analytics_ro, admin (DBA only).
- Grant least privilege; avoid superuser for apps.

## Network
- Private endpoint for prod/uat; disable public network access.
- SSL required; verify server certs.

## Secrets
- KV secret reference for passwords when used; prefer AAD auth for connection strings.

## Ops
- Rotate passwords quarterly or on incident.
- Audit logs to Log Analytics; alert on failed logins and superuser use.

