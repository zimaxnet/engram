# AuthN/AuthZ SOP - CI/CD

## Identity
- Use GitHub Actions OIDC to Azure; no stored SP secrets.
- Federated credentials scoped to repo/branch/environment.

## Permissions
- Pipeline principal: deploy roles on RG, `Key Vault Secrets User`, `AcrPush`, `Website Contributor` for SWA if needed.
- No data-plane access (Postgres/Storage) from pipeline unless for migrations with MI.

## Secrets
- Store minimal secrets in GitHub Actions secrets (e.g., SWA token if required); prefer none.
- Use Key Vault for environment secrets; fetch via MI where possible.

## Approvals
- Env protection rules: require approvers for uat/prod; manual gates for prod.

## Auditing
- Monitor role assignments for pipeline principal; logins via `azure/login`; alert on failed federated auth.
# SOP: CI/CD (GitHub Actions)
- Auth: OIDC federation with Azure (`azure/login@v2`); no stored client secrets.
- Scope: per-env service principal with least privilege (RG-level deploy, KV Secrets User, ACR push).
- Approvals: required for uat/prod environments; protected branches.
- Secrets: store minimal in GH env secrets (tenant, subscription, clientId if needed); no keys.
- Logging: capture deployment logs; alert on failed logins or forbidden deployments.
# Auth SOP – CI/CD

## Identity
- Use GitHub Actions OIDC to Azure; no stored client secrets.
- Federated credentials scoped to repo/branch and subscription.

## Permissions
- Pipeline principal roles: deploy RG scope, `AcrPush`, `Key Vault Secrets User`, minimal `Container Apps Auth`/`AKS Cluster Admin` only where needed.
- Environment approvals for uat/staging/prod.

## Secrets
- None in repo; use KV for transient secrets if required; prefer MI access.

## Auditing
- Enable GitHub environment protection and audit logs; Azure sign-in logs for pipeline principal.
# SOP: CI/CD (GitHub Actions)

## Identity
- Use OIDC federation to Azure; no long-lived client secrets.
- Federated creds scoped to repo/branch and subscription/resource group.

## Permissions
- Deployment principal: minimal roles (RG Contributor, AcrPush, KV Secrets User, Container App/AKS deploy roles).
- Separate principals per environment with approvals for uat/prod.

## Secrets
- Store only non-sensitive config in repo; no Azure secrets in GitHub.

## Monitoring
- Audit GitHub deployments; Azure activity logs for role assignments and deployments; alert on failed logins.

