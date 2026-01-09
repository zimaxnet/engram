# Security Hardening Implementation Plan (Priority Focus)

**Goal:** Execute the "Shortest Path to Enterprise Acceptable" by addressing the Top 5 Priorities identified in the Gap Analysis.

## User Review Required

> [!IMPORTANT]
> **Admin Strategy Change**: We are moving away from "Derek-Only" to a "Primary + Break-Glass" model to satisfy business continuity requirements.

> [!WARNING]
> **Strict Tenant Enforcement**: The system will explicitly reject any token that does not match the `zimaxlc` tenant ID. Ensure your local environment is configured with valid `zimaxlc` credentials.

## Priority 1: Multi-Tenant Identity & RBAC Upgrade (App Roles)

**Objective:** Replace fragile Group Claims with stable App Roles and enforce strict Tenant Whitelisting.

#### [MODIFY] [auth.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/api/middleware/auth.py)

- **Tenant Whitelisting**:
  - Add `ALLOWED_TENANT_IDS` configuration.
  - Inspect `tid` claim -> Reject if not in allowlist.
  - Inspect `iss` claim -> Verify it matches `https://login.microsoftonline.com/{tid}/v2.0` or CIAM equivalent.
- **Audience & Authorized Party**:
  - Validate `aud` matches API URI.
  - Validate `azp` (if present) matches known Client IDs.
- **RBAC Transition**:
  - Remove/Deprecate legacy Group Claim logic.
  - Map `roles` claim to internally defined roles:
    - `Engram.SuperAdmin` -> `Role.ADMIN`
    - `Engram.Admin` -> `Role.ADMIN` (Break-glass)
    - `Engram.Department.*` -> Mapped to `SecurityContext.department_ids`

## Priority 2: Admin Resilience (Break-Glass + PIM)

**Objective:** Mitigate Single Point of Failure risk for administration.

#### [NEW] [docs/security/admin-access-policy.md](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/docs/security/admin-access-policy.md)

- Define the **Primary Admin** (Derek).
- Define the **Break-Glass Admin** (Service Account with offline credentials).
- Define **PIM Eligibility** requirements for high-privilege roles.

## Priority 3: Write-Time & Read-Time Authorization Enforcement

**Objective:** Prevent "Write-Time Forgery" and ensure strict isolation.

#### [MODIFY] [ingest.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/api/routers/ingest.py)

- **Write Protection**:
  - Remove `department_id` from input Pydantic models (User cannot send it).
  - In the route handler, derive `department_id` *only* from `request.user.department_ids`.
  - If user has multiple departments, require explicit query param *validated* against their token entitlements.

#### [MODIFY] [search.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/api/routers/search.py) (or equivalent)

- **Read Protection**:
  - Force-inject `user.department_ids` into every vector search filter.
  - Ensure `tenant_id` is mandatory in every filter.

## Priority 4: Database Isolation (RLS)

**Objective:** "Defense in Depth" at the data layer.

#### [MODIFY] [schema.sql] (To be located)

- **RLS Policies**:
  - Enable RLS on `documents`, `chunks`.
  - Create Policy: `tenant_isolation_policy`: `CHECK (tenant_id = current_setting('app.current_tenant')::uuid)`
  - Create Policy: `dept_isolation_policy`: `CHECK (department_id = ANY(string_to_array(current_setting('app.current_user_depts'), ',')))`

#### [MODIFY] [database.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/core/database.py)

- **Session Injection**:
  - Update connection checkout logic (or middleware) to execute:
        `SET LOCAL app.current_tenant = '...';`
        `SET LOCAL app.current_user_depts = '...';`
  - Before every request processing.

## Priority 5: Audit Logging

**Objective:** Tamper-resistant evidence.

#### [NEW] [audit.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/core/audit.py)

- **AuditLogger Class**:
  - Structured JSON output.
  - Integration with Azure Monitor (opencensus/azure-monitor extension).
- **Instrumentation**:
  - Log every `AUTH_FAILURE`.
  - Log every `SENSITIVE_ACCESS` (Admin routes).
  - Log `RETRIEVAL_EVENT` (which docs were returned to whom).

---

## Execution Order

1. **Auth Hardening**: `auth.py`
2. **AuthZ Enforcement**: `ingest.py` / `memory_client.py`
3. **Audit Logging**: `audit.py`
4. **Database RLS**: `schema.sql` / `database.py` (Complexity High)
