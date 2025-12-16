# AuthN/AuthZ SOP - Storage (Blob)

## Access
- Use Managed Identity with `Storage Blob Data Reader/Contributor` as needed.
- No account keys in prod; SAS only short-lived and server-generated.

## Network
- Prod/UAT: private endpoints; disable public access; min TLS1.2.
- Staging/Test: public allowed only if needed; prefer private when possible.

## Containers
- No public containers in prod; versioning enabled; soft delete for blobs.

## Monitoring
- Enable storage logs to Log Analytics; alert on anonymous access attempts or high auth failures.
# SOP: Storage (Blob)
- Auth: Managed Identity with `Storage Blob Data Reader/Contributor` as needed.
- Network: private endpoints in uat/prod; disable public containers; HTTPS only.
- SAS: only short-lived, user-scoped tokens; generate server-side; log issuance.
- Encryption: server-side with MS-managed keys; consider CMK for prod archives.
- Auditing: enable diagnostics to Log Analytics; alert on anonymous/public access attempts.
# Auth SOP – Storage (Blob)

## AuthN/Z
- Use MI with `Storage Blob Data Reader/Contributor` scoped to container.
- Disable public access to containers; prod uses private endpoint.
- SAS only for short-lived, user-scoped scenarios; generate server-side.

## Network
- Prod: private endpoint, HTTPS only, min TLS1.2.
- Lower env: allow AzureServices; consider IP allowlist for admin tools.

## Auditing
- Enable Storage logs to Log Analytics; alert on anonymous access attempts.
# SOP: Storage (Blob)

## AuthN/Z
- Use Managed Identity with RBAC (`Storage Blob Data Reader/Contributor`) per app need.
- No storage account keys in prod; SAS only short-lived and server-issued.

## Network
- Private endpoints for prod/uat; disable public blob access.
- TLS enforced; minimum TLS 1.2.

## Data Controls
- Container-level least privilege; disable anonymous access.

## Monitoring
- Enable Storage logs to Log Analytics; alert on anonymous or key-based access in prod.

