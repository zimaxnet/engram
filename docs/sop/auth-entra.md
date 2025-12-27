# AuthN/AuthZ SOP - Azure Entra ID

## Objectives
- Centralize user auth, app roles, and conditional access for all environments.

## App Registrations (per env)
- Names: `engram-api-{env}` with App ID URI `api://engram-{env}`.
- Roles: Admin, Analyst, PM, Viewer.
- Scope: `user_impersonation`.
- Redirect URIs: SWA and local dev callbacks; enable SPA implicit ID token only if needed for SWA.

## Certificates/Secrets
- Prefer no client secrets for backends; use MI. If SP needed (CI/CD), store secret in Key Vault non-prod only; rotate 90d.

## Conditional Access (prod/uat/staging)
- Require MFA for Admin/PM; block legacy; restrict sign-in from risky locations; require compliant/hybrid joined devices for prod admin.

## Group-to-Role Mapping
- Use Entra groups per role per env; assign groups to app roles; avoid direct user role assignment.

## Token Validation (API/MCP)
- Issuer: tenant; Audience: `api://engram-{env}`; validate roles claim -> internal roles.
- Lifetime: default 60m; rely on refresh at client; enforce clock skew ≤5m.

## Logging/Auditing
- Track sign-in logs, app role assignments, service principal consent; alert on unexpected consent or mass assignment changes.
# SOP: Azure Entra ID
- App registrations per environment: `engram-api-{env}` with App ID URI `api://engram-{env}`.
- Define app roles: Admin, Analyst, PM, Viewer. Map Entra groups to roles.
- Expose scope `user_impersonation`. Use v2 endpoints.
- Conditional Access: MFA for Admin/PM; block legacy auth; sign-in risk policy for prod.
- Token settings: access token 60m, refresh 24h; assign to SWA/API clients.
- Service principals: only for CI/CD via OIDC federation; avoid client secrets where possible.
- Rotation: client secrets (if any) 90d; verify reply URLs and logout URLs per env.

# Auth SOP – Azure Entra ID

## App Registrations (per env)
- Apps: engram-api-{dev,test,uat,staging,prod}
- Expose API: `api://engram-{env}`
- Roles: Admin, Analyst, PM, Viewer
- Scope: `user_impersonation`

## Conditional Access
- Prod: MFA for Admin/PM; block legacy auth; sign-in risk policy.
- Lower env: optional MFA; restrict admin group.

## Group → Role Mapping
- Create Entra groups per role per env; assign to app roles.

## Token Guidance
- Audience = App ID URI; Issuer = tenant; validate `scp`/roles.
- Lifetime: default; no refresh token reuse outside client apps.

## Service Principals
- Only for CI/CD with OIDC; no client secrets at rest.
# SOP: Azure Entra ID

## Scope
- App registrations per env (dev/test/uat/staging/prod) with App ID URI `api://engram-<env>`.
- Roles: Admin, Analyst, PM, Viewer.

## Procedures
- Create app registration + expose API (user_impersonation) + app roles.
- Assign groups to roles; use PIM for Admin.
- Configure optional claims: roles, aud, preferred_username.
- Conditional Access: MFA for Admin/PM; block legacy; require compliant device for prod.
- Service principals: only CI/CD; use OIDC federated creds; no client secrets where possible.

## Tokens
- Audience = App ID URI; Issuer = tenant. Lifetime per policy; enable token replay detection via CA.

## Monitoring
- Entra sign-in logs; risky sign-in alerts; review monthly.

