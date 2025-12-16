# AuthN/AuthZ SOP - Static Web App (SWA)

## Authentication
- Use Entra provider; configure client ID/secret via SWA settings.
- Require authenticated for `/api/*` routes; align roles with app roles.

## CORS/Origins
- Allowed origins limited to env domains; no wildcards in prod.

## Tokens
- Frontend obtains tokens and forwards to API; avoid storing tokens in localStorage (use session storage or MSAL cache defaults).

## Secrets
- Store provider secrets in SWA configuration (not repo); rotate 180d.

## Logging
- Enable SWA auth logs; monitor failed logins and role mismatches.
# SOP: Static Web App (SWA)
- Auth: Entra provider configured; enforce login; routes require `authenticated`.
- Roles: map app roles if exposed; otherwise treat SWA as public UI but API requires token.
- CORS: align with backend allowed origins; no wildcard in prod.
- Secrets: store AAD client ID/secret in SWA settings; never in repo.
- API calls: include bearer token from Entra; validate audience for API.
# Auth SOP – Static Web App (SWA)

## Auth
- Configure Entra provider; require authenticated role for API routes.
- Map Entra app per env; use env settings for client ID/secret.

## Routes
- Protect `/api/*` with `allowedRoles: ["authenticated"]`.
- Restrict admin pages to Entra roles via frontend checks.

## Tokens
- Frontend obtains user token and calls backend with bearer token; no embedded secrets.

## CORS
- Allow only env-specific domains and SWA default hostname; no `*` in prod.
# SOP: Static Web App (SWA)

## AuthN
- Entra provider configured with tenant issuer.
- Require authenticated for `/api/*` routes; anonymous only for public assets.

## Tokens
- Frontend obtains bearer token and forwards to API.

## Config
- `staticwebapp.config.json` checked in; secrets via SWA settings (client ID/secret).
- Allowed origins restricted to SWA domain + custom domain.

## Monitoring
- Enable SWA diagnostics; alert on auth failures.

