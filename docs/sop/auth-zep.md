# AuthN/AuthZ SOP - Zep

## Authentication
- API key per environment; store in Key Vault; inject via secret ref.
- Long term: migrate to OIDC/MI if supported.

## Network
- Internal-only ingress in Container Apps/AKS; no public exposure.
- In prod, access only from backend/worker namespaces; enforce via network policies.

## Data
- Postgres DSN uses TLS; credentials from Key Vault; prefer separate DB/user.

## Rotation
- Rotate API key 90d; restart backend/worker after rotation.

## Monitoring
- Health checks `/healthz`; log auth failures; ship app logs to Log Analytics via ACA/AKS.
# SOP: Zep (Memory)
- Auth: API key required; store in Key Vault; inject via secret ref.
- Network: internal-only ingress (ACA) or cluster-internal service (AKS); no public exposure.
- RBAC: if multi-tenant features available, map to env/tenant; otherwise isolate by environment.
- Rotation: rotate API key every 60 days; propagate to backend/worker; restart apps.
- Auditing: enable access logs; alert on failed auth; monitor unusual volume.
# Auth SOP – Zep (Self-hosted)

## AuthN
- API key required; store in Key Vault; inject via secretRef.
- Long term: prefer internal-only access; no public ingress.

## Network
- ACA: `external: false` (internal FQDN). Prod: private access only; reachable from backend/worker.
- Optionally IP restrict if ever exposed.

## Data Access
- DB auth via Postgres AAD or strong password; SSL required.

## Rotation
- Rotate API key every 90 days; update KV and restart backend/worker.
# SOP: Zep (Self-hosted)

## AuthN
- Use API key stored in Key Vault; inject to backend/worker as secret ref.
- No public ingress; internal-only Container Apps/AKS service.

## Network
- Private/internal ingress only; no public exposure.
- Allow only backend/worker traffic via network policies (AKS) or ACA internal.

## Rotation
- Rotate API key quarterly or on incident; store only in KV.

## Monitoring
- Enable request logs; alert on auth failures; validate API key usage limited to app identities.

