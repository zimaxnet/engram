## Engram Environment AuthN/AuthZ Guidance (NIST AI RMF–Aligned)

### Purpose
Provide a public-safe, environment-specific security posture for deploying and validating the Engram engine across:
- **Dev**
- **Test**
- **Staging (POC validation)**
- **UAT**
- **Prod**

This guide focuses on **authentication (AuthN)**, **authorization (AuthZ)**, and the supporting controls needed to satisfy a pragmatic interpretation of **NIST AI RMF** while enabling fast validation.

### Key principle: avoid “double auth”
Choose **one** system-of-record for identity enforcement:
- **Recommended**: app-layer auth in FastAPI/FastMCP (portable across customer tenants).
- Only add edge/platform auth (WAF/APIM/Ingress) when you need it, and ensure it does not block requests before the app if the app is expected to enforce auth.

If you enable platform auth and app auth simultaneously without tight alignment, you will get confusing 401/403 behavior and incomplete logs.

### Definitions
- **App-layer auth**: Entra/OIDC JWT validation implemented in the FastAPI app (`backend/api/middleware/auth.py`).
- **Platform/edge auth**: identity enforcement provided by the hosting layer (e.g., “Authentication” feature).
- **Workload identity**: Managed Identity or Kubernetes workload identity used by services to access Azure resources.

### Environment variables (portable, public-safe)
To avoid collisions between Entra and Managed Identity:
- **`AZURE_AD_CLIENT_ID`**: Entra app registration client ID used by the API to validate JWT audience.
- **`AZURE_TENANT_ID`**: Entra tenant ID for issuer validation.
- **`AZURE_CLIENT_ID`**: user-assigned Managed Identity client ID used by Azure SDKs (DefaultAzureCredential) to select the correct MI.
- **`AUTH_REQUIRED`**: `true|false`. When `false`, the API bypasses auth (POC only).

### NIST AI RMF lens (how this maps)
This guide maps to the four NIST AI RMF functions:
- **Govern**: roles, policy, separation of duties, change control, approvals.
- **Map**: data classification, environment risk profile, trust boundaries.
- **Measure**: telemetry, audit logs, security testing and acceptance criteria.
- **Manage**: access control implementation, incident response, rotation, rollback.

---

## Environment matrix (recommended defaults)

| Environment | Primary goal | App-layer Auth | Platform/edge Auth | Data policy | Notes |
|---|---|---:|---:|---|---|
| Dev | developer velocity | Optional | Off | synthetic only | allow localhost CORS |
| Test | CI validation | Optional or Required | Off | synthetic only | deterministic tests |
| Staging (POC) | prove system works | Off (via `AUTH_REQUIRED=false`) | Off | synthetic or de-identified | fastest validation |
| UAT | production-like verification | Required | Prefer WAF/APIM (no auth at edge initially) | masked/anonymized | match prod controls |
| Prod | secure operations | Required | WAF/APIM + optional edge auth | real data | least privilege + private networking |

---

## Staging (POC validation) – minimal friction, measurable safety

### Intended use
Demonstrate end-to-end functionality (UI → API → memory/workflows) using non-sensitive data.

### Required controls (NIST AI RMF)
- **Govern**: declare POC scope, allowed users, and data classification (synthetic / de-identified).
- **Map**: document trust boundary: external ingress → API → internal services.
- **Measure**: enable request logging + error logging; confirm smoke tests run.
- **Manage**: enforce limited exposure (time-boxed environment, IP allowlist where possible, rotate any temporary secrets after demo).

### Configuration
- **Disable platform/edge auth** so requests reach the app.
- Set:
  - `AUTH_REQUIRED=false` on the API.
  - Keep `AZURE_CLIENT_ID` reserved for Managed Identity selection (optional for POC).
  - Do not require user tokens for POC validation.

### POC smoke test checklist
- Health:
  - `GET /health` returns 200
- Agents:
  - `GET /api/v1/agents` returns 200
- Chat (validates LLM gateway config):
  - `POST /api/v1/chat` returns 200
- Memory (validates Zep wiring):
  - `POST /api/v1/memory/search` returns 200 (empty results acceptable for POC)
- Workflows:
  - `GET /api/v1/workflows` returns 200 (mock acceptable if Temporal not configured)
- MCP reachability:
  - `GET /api/v1/mcp/sse` returns 200/stream start

### Exit criteria (POC complete)
- API health + agents endpoints reachable externally.
- Chat returns a valid response.
- Memory endpoints respond without errors (even if empty).
- Logs show successful request/response entries.

---

## Dev – fast iteration with guardrails

### Recommended controls (NIST AI RMF)
- **Govern**: developer access policy; no production secrets on dev machines.
- **Map**: identify dev-only bypasses; document them.
- **Measure**: run unit tests and basic API contract tests.
- **Manage**: secrets in local `.env` only for dev; never commit; periodic rotation.

### Configuration
- `ENVIRONMENT=development`
- Allow `X-Dev-Token` (dev-only) and/or `AUTH_REQUIRED=false` for local runs.
- CORS includes localhost.

---

## Test – deterministic CI validation

### Recommended controls (NIST AI RMF)
- **Govern**: define test acceptance criteria (golden thread).
- **Map**: use seeded synthetic datasets.
- **Measure**: run API contract tests, lint, and deterministic end-to-end checks.
- **Manage**: block external dependencies or use mocks where possible.

### Configuration
- Prefer `AUTH_REQUIRED=false` to reduce test flake, or keep `AUTH_REQUIRED=true` with a test identity provider.
- Ensure tests never require real customer data.

---

## UAT – production-like verification (pre-prod)

### Recommended controls (NIST AI RMF)
- **Govern**: UAT approval process; role-based access; change control.
- **Map**: document integration points: Zep, Temporal, Postgres, Storage, LLM gateway.
- **Measure**: run golden-thread suite; monitor auth failures and latency.
- **Manage**: incident playbook ready; secret rotation validated; rollback plan rehearsed.

### Configuration
- `AUTH_REQUIRED=true`
- Use Entra/OIDC with:
  - `AZURE_AD_CLIENT_ID` (API app registration)
  - `AZURE_TENANT_ID`
- Keep platform auth off initially; put WAF/APIM in front for rate limiting and threat protection.
- Apply private endpoints where feasible; restrict internal services to internal ingress.

---

## Prod – secure operations (customer tenant–ready)

### Recommended controls (NIST AI RMF)
- **Govern**: least privilege; separation of duties; approvals; periodic access review.
- **Map**: formal threat model, data classifications, and trust boundaries.
- **Measure**: continuous monitoring, audit logs, detection/response metrics.
- **Manage**: incident response, key rotation, break-glass controls, DR/backup.

### Configuration
- `AUTH_REQUIRED=true`
- Use Entra/OIDC issuer + audience validation via:
  - `AZURE_AD_CLIENT_ID`
  - `AZURE_TENANT_ID`
- Use Managed Identity / workload identity for Azure resources:
  - Keep `AZURE_CLIENT_ID` for MI selection only.
- Network hardening:
  - WAF/APIM in front of public endpoints
  - internal-only ingress for Zep/Temporal server
  - private endpoints for data stores (as available)
- Strong AuthZ:
  - Entra app roles/groups mapped to internal roles
  - explicit scope checks for sensitive actions

---

## Customer tenant deployment path (portable identity)

### Customer-owned identity (recommended)
1) Customer creates an Entra app registration in their tenant for the Engram API.
2) Customer defines roles/scopes and assigns groups/users.
3) Deploy Engram infra into customer subscription/resource group.
4) Configure Engram API with customer tenant settings:
   - `AZURE_TENANT_ID=<customerTenantId>`
   - `AZURE_AD_CLIENT_ID=<customerApiAppClientId>`
5) Workload identity uses customer Managed Identities for Key Vault/Storage/AI services.

### Adding CIAM / social identity later
- Use Entra External ID (CIAM) or an equivalent OIDC provider.
- Federate Google/GitHub/Microsoft into CIAM.
- App remains unchanged; only issuer/audience changes and claim mapping (roles/scopes).

---

## Operational hygiene checklist (all environments)
- Keep platform auth and app auth from conflicting; decide which layer enforces identity.
- Keep Entra client ID separate from Managed Identity client ID.
- Never use real customer data in dev/test/staging unless explicitly approved and masked.
- Rotate secrets after POC; validate Key Vault access and audit logs.
- Log auth failures and include correlation IDs (no unnecessary PII).

