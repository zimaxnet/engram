# AuthN/AuthZ SOP - Temporal

## Environments
- Dev/Test/UAT/Staging on ACA: internal ingress only for server; UI public but should be behind basic auth/API key; restrict by IP where possible.
- Prod on AKS: mTLS between workers and server; UI behind OIDC (Entra) and internal/VPN.

## Auth Options
- Server: mTLS for gRPC in prod; certs from Key Vault or Azure Key Vault-backed CSI in AKS.
- UI: OIDC to Entra (preferred); fallback basic auth only in lower envs.

## Roles/Namespaces
- Use namespaces per env; restrict task queue access by role where supported.
- Admin users for namespace ops; workers have minimal permissions.

## Network
- Internal service only; deny public gRPC in prod; UI ingress through WAF/VPN.

## Secrets
- Store any UI basic auth/API key in Key Vault non-prod; certs in Key Vault; mount via CSI in AKS.

## Logging
- Enable audit/visibility if available; ship logs to Log Analytics.
# SOP: Temporal
- Environments: internal ingress only for server; UI restricted.
- Dev/Test/UAT/Staging (ACA):
  - Server: internal-only; no external ingress.
  - UI: basic auth/API key; restricted origins; optional IP allow list.
- Prod (AKS):
  - mTLS between workers and server; certs from Key Vault.
  - UI: OIDC with Entra; role separation (admin/viewer).
  - Namespaces: dedicated per env; restrict task queue access to worker MI.
- Auditing: enable server metrics/logs; alert on auth failures; restrict codec server if enabled.

# Auth SOP – Temporal

## In ACA (dev/staging/uat)
- Server ingress: internal only; UI external allowed with basic auth/API key.
- Restrict UI by IP allowlist if exposed.

## In AKS (prod)
- mTLS between workers and server; OIDC/SAML for UI access.
- Namespace-level permissions: admin vs worker vs viewer.
- NetworkPolicy: allow worker→server gRPC; deny all else; UI behind WAF/VPN.

## Secrets
- Store creds/certs in Key Vault; inject via CSI/secret ref; no inline secrets.

## Auditing
- Enable server metrics/logs to Log Analytics; monitor failed auth and namespace ops.
# SOP: Temporal

## AuthN
- ACA (dev/staging/uat): internal ingress for server; UI may be external with basic auth.
- AKS (prod): mTLS between workers and server; OIDC/basicauth for UI via ingress controller.

## AuthZ
- Namespace-level permissions: admins (tctl), workers (task queue), viewers (read-only UI).

## Network
- Keep server gRPC internal; UI behind WAF/ingress with auth; restrict CIDR.

## Secrets
- DB creds from KV; no inline secrets.

## Ops
- Audit tctl usage; alert on failed auth; rotate UI basic auth (if used) every 90 days.

