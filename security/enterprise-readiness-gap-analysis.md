# Enterprise Readiness Gap Analysis & Remediation Plan

**Date:** 2026-01-08
**Context:** Security Review Feedback Integration
**Target:** Enterprise-Grade Acceptance (NIST AI RMF aligned)

---

## Executive Summary

This document captures the specific gaps and acceptance blockers identified during the Enterprise Security Review. It serves as the primary reference for the remediation roadmap.

## 1. Multi-Tenant Identity Design (Trust Boundary)

**Gap:** Relying on "multitenant" App Registration alone is insufficient.
**Requirement:** Explicit Tenant Whitelisting & Issuer Validation.

### Remediation Checklist

- [ ] **`tid` Allowlist:** Enforce strict check that token `tid` matches authorized tenant (`zimaxlc`).
- [ ] **Issuer (`iss`) Validation:** Validate `iss` matches specific V2 endpoint pattern for the tenant.
- [ ] **Audience (`aud`) Validation:** Ensure `aud` matches the Application ID URI (not generic).
- [ ] **Authorized Party (`azp`) Check:** Validate that the client requesting the token is authorized (prevents replay).
- [ ] **Authority:** Use `organizations` endpoint (strict), avoid `common`.
- [ ] **Group Claims Strategy:** Move from "Group Claims" in token to **App Role Assignments** to avoid overage/limits.

## 2. Administrator Model

**Gap:** "Derek-only" admin is a Business Continuity Risk (Single Point of Failure).
**Requirement:** 2-Admin Rule, Break-glass, and PIM.

### Remediation Checklist

- [ ] **Break-glass Admin:** Create secondary admin account managed under strict policy (offline password).
- [ ] **PIM Eligibility:** Configure Admin roles as "Eligible" requiring Just-In-Time (JIT) elevation (if P2 license available) or procedural JIT.
- [ ] **Separation of Duties:** Differentiate roles:
  - **RBAC Admin:** Assigns permissions.
  - **Audit Admin:** Views logs (Read-Only).
  - **Data Steward:** Approves datasets.

## 3. Authorization Enforcement (Read & Write)

**Gap:** Potential for "Write-time Forgery" (user setting `department_id` in payload).
**Requirement:** AuthZ at every path.

### Remediation Checklist

- [ ] **Write Enforcement:** Backend derives `department_id` strictly from Token, ignores/overwrites payload.
- [ ] **Read Enforcement:** Backend `search()` filters strictly by Token-derived attributes.
- [ ] **Isolation Unit Definition:** Formalize hierarchy: `Tenant` > `Department` > `Project` > `Document`.

## 4. Database Isolation (Row-Level Security)

**Gap:** Application-level filtering is prone to "leakage" bugs.
**Requirement:** Database-level RLS (Row-Level Security).

### Remediation Checklist

- [ ] **RLS Coverage:** Enable on `documents`, `chunks`, `embeddings`, and valid `join` tables.
- [ ] **Service Identity:** Implement "Set Local Session Variable" pattern (`app.current_tenant`, `app.current_dept`) for RLS policies.
- [ ] **No Bypass:** Ensure connection pool does not use `SECURITY DEFINER` privileges by default.
- [ ] **Embedding Protection:** Ensure vector similarity checks also respect RLS (filter *before* or *during* vector search).

## 5. Identity Assurance

**Gap:** Need to enforce strong authentication on the IDP side.
**Requirement:** Conditional Access attributes.

### Remediation Checklist

- [ ] **MFA Enforcement:** Verify MFA claim in token or enforce at IDP.
- [ ] **Phishing-Resistant MFA:** Require FIDO2/Hello for Admins.
- [ ] **Device Compliance:** (Future) Require Compliant/Hybrid Joined device state.

## 6. Audit & Evidence

**Gap:** Current logging is likely ephemeral or insufficient for forensics.
**Requirement:** Tamper-resistant, centralized audit trail.

### Remediation Checklist

- [ ] **Centralized Shipping:** Ship logs to Azure Monitor / Log Analytics.
- [ ] **Structured Events:** Log `Who`, `What`, `When`, `Where`, `Decision`.
- [ ] **AI-Specific Audit:** Log Retrieval Context (Doc IDs, Chunks), Prompt Injection Flags, Data Class violations.
- [ ] **Admin Audit:** Log all Role/Policy changes.

## 7. Data Protection & Egress

**Gap:** Exfiltration risk.
**Requirement:** Private endpoints & Network controls.

### Remediation Checklist

- [ ] **Private Link:** Use Private Endpoints for PostgreSQL, Key Vault, Storage, Search.
- [ ] **Egress Control:** Restrict outbound traffic via FW/NAT.
- [ ] **Key Vault Hardening:** Managed Identity Only (No Secrets in Env). Soft Delete + Purge Protection enabled.
- [ ] **Encryption:** CMK (Customer Managed Keys) roadmap for regulated clients.

## 8. Agentic Controls

**Gap:** Undefined agent capabilities.
**Requirement:** Least-privilege for Agents.

### Remediation Checklist

- [ ] **Tool Authorization:** Per-Agent / Per-User tool whitelisting.
- [ ] **Action Boundaries:** Read-Only vs. Destructive action definition.
- [ ] **HITL (Human-in-the-Loop):** Require approval for high-risk actions.
- [ ] **Untrusted Content:** Treat retrieved RAG content as untrusted user input.

## 9. Secure SDLC

**Gap:** Supply chain risks.

### Remediation Checklist

- [ ] **CI Security:** Add SAST/SCA scanning.
- [ ] **Container Security:** Image scanning + SBOM.
- [ ] **Dependency Pinning:** Freeze versions.

## 10. Documentation Artifacts

**Gap:** "The missing enterprise artifacts".

### Remediation Checklist

- [ ] **Security Architecture Diagram**
- [ ] **RBAC Model Definition**
- [ ] **Data Handling Policy**
- [ ] **Incident Response Runbook**
- [ ] **BCDR Plan**

---

## Implementation Priorities (Immediate)

1. **RBAC Upgrade:** Switch from Group Claims to App Roles.
2. **Admin Resilience:** Implement Break-glass + PIM model.
3. **Full Authorization:** Enforce Write/Read AuthZ + RLS.
4. **Audit Logging:** Tamper-resistant central logging.
5. **Network Hardening:** Egress controls + Private Endpoints.
