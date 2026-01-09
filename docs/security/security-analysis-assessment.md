# Security Analysis & Assessment: Engram Permissions & Governance

**Date:** 2026-01-08
**Author:** Engram Platform Architect
**Framework:** NIST AI Risk Management Framework (AI RMF 1.0)
**Context:** Multi-Tenant Enterprise Agentic System (Zimax Networks LC)

---

## 1. Multi-Tenant Identity Architecture

**Scenario:** A split-tenant environment where resources reside in one tenant (`engramai`) and users reside in another (`zimaxlc`).

### A. Tenant Roles

1. **Resource Tenant (`engramai.onmicrosoft.com`):**
    * **Hosts:** Azure Container Apps (Engram Backend/Frontend), Key Vault, PostgreSQL, Search, Storage.
    * **Identity Source:** Contains the **App Registration** definition for Engram.
    * **Role:** The "Service Provider".
2. **User Tenant (`zimaxlc.onmicrosoft.com`):**
    * **Hosts:** Corporate Users (Derek + Employees), Security Groups (Engineering, Sales, etc.).
    * **Identity Source:** Source of Truth for user identities.
    * **Role:** The "Identity Provider".

### B. The "Bridge" Mechanism

To allow `zimaxlc` users to access `engramai` resources securely:

1. **Multi-Tenant App Registration:** The Engram App in `engramai` must be configured as *"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant)"*.
2. **Enterprise Application (Service Principal):** When Derek (admin) first logs in or consents, a Service Principal for Engram is instantiated in the `zimaxlc` tenant.
3. **Authentication Flow:**
    * User logs in via `zimaxlc` credentials.
    * Microsoft Entra ID issues a token signed by `zimaxlc` (Issuer).
    * Engram Backend (`engramai`) validates the token signature using the OIDC Discovery keys from `zimaxlc`.

### C. Analysis of Current Implementation (`auth.py`)

* **Strengths:**
  * ✅ Validates standard JWT fields (iss, aud, exp, nbf).
  * ✅ Supports `AZURE_AD_EXTERNAL_ID` (CIAM) and Workforce tenants.
  * ✅ Maps basic App Roles (`Admin`, `Analyst`, etc.) to internal Pydantic models.
* **Gaps:**
  * ❌ **No Group Claim Processing:** `auth.py` currently looks for `roles` (App Roles) but does not extract or process **Security Group IDs** (`groups` claim) which are required for Departmental RBAC.
  * ❌ **Tenant Whitelisting:** Currently allows "common" or configured tenant. Need Strict Tenant Whitelisting to prevent *other* unauthorized tenants from logging in even if they result in valid tokens.

---

## 2. Access Control Model (RBAC) & Privilege Separation

### A. Administrator Isolation (The "Derek" Rule)

**Objective:** Designate Derek as the *only* user capable of setting permissions.

**Strategy:**

1. **App Role Assignment:**
    * Define a specific App Role in the Manifest: `Engram.SuperAdmin`.
    * In the `zimaxlc` Entra ID portal -> Enterprise Applications -> Engram -> **Users and groups**.
    * Assign **ONLY Derek's User Account** to the `Engram.SuperAdmin` role.
    * Set "User Assignment Required?" to **Yes**. This blocks *everyone else* by default.
2. **Code Enforcement:**
    * Update `auth.py`: If route requires `Role.ADMIN`, strictly check for the `Engram.SuperAdmin` role claim.

### B. Departmental Security Groups

**Objective:** Administer permissions by Department (Sales, Engineering, etc.).

**Strategy:**

1. **Azure AD Groups:** Create Security Groups in `zimaxlc`:
    * `SG_Engram_Engineering` (Object ID: `uuid-1`)
    * `SG_Engram_Sales` (Object ID: `uuid-2`)
    * `SG_Engram_Executive` (Object ID: `uuid-3`)
2. **Token Configuration:**
    * Configure the Engram App Registration to emit **Group Claims** (Security groups) in the token.
    * *Note:* Tokens contain Group *Object IDs* (UUIDs), not names, to prevent mutable name collisions.
3. **Mapping Layer (Backend):**
    * Backend maintains a mapping (Env Var or DB):

        ```python
        DEPARTMENT_MAPPING = {
            "uuid-1": "Engineering",
            "uuid-2": "Sales"
        }
        ```

    * When storing Memories/Documents, tag them with `department_id`.
    * At query time (RAG), filter results: `WHERE doc.department_id IN user.department_ids`.

---

## 3. NIST AI RMF Alignment (1.0)

See: *NIST AI 100-1, Artificial Intelligence Risk Management Framework*

### A. GOVERN (Cultivate a culture of risk management)

* **1.1 Policies:** Define that *Authentication is Mandatory* (`AUTH_REQUIRED=True`). Bypass is only for "POC/Dev" and flagged heavily in logs.
* **1.6 Inventory:** Maintain inventory of all AI Agents (Elena, Sage) and their access scopes (defined in Layer 4 Memory).

### B. MAP (Context recognition and risk identification)

* **Context:** AI Agents access proprietary data (Class A/B).
* **Risk:** "Context Leakage" (e.g., Sales Agent revealing Engineering secrets).
* **Mitigation:** The **Departmental RBAC** acts as the primary firewall. Memory retrieval queries must be strictly scoped to the user's Department ID.

### C. MEASURE (Assess, analyze, and track AI risks)

* **Metric:** Failed Access Attempts (401/403 logs in Container Apps).
* **Metric:** Unauthorized Department Cross-Talk (Auditing retrieval logs for cross-department queries).

### D. MANAGE (Prioritize and act upon risks)

* **3.2 Treatment:** Implement **Hard Filtering** in the Vector Database (PGVector).
  * *Bad:* Relying on the LLM to "pretend" not to know secrets.
  * *Good (NIST Compliant):* The LLM never sees the secrets because the RAG retrieval filtered them out at the database level.

---

## 4. Implementation Roadmap (Gaps to Close)

| Phase | Action Item | Priority |
|-------|-------------|----------|
| **1** | **Strict Tenant Validation:** Modify `auth.py` to reject tokens where `tid` != `zimaxlc_tenant_id` (unless explicitly whitelisted). | 🔥 Critical |
| **2** | **App Role for Admin:** Create `Engram.SuperAdmin` role in Azure AD and enforce in `backend/`. | 🔥 Critical |
| **3** | **Group Claim Logic:** Update `EntraIDAuth` to extract `groups` claim and map to Departments. | 🟡 High |
| **4** | **PGVector RLS:** Implement Row-Level Security (RLS) or metadata filtering in Postgres for Document/Chunk tables. | 🟡 High |
