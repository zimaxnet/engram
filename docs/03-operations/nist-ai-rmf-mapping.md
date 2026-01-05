---
layout: default
title: "NIST AI Risk Management Framework (RMF) Compliance Map"
parent: "Operations"
---

# NIST AI Risk Management Framework (RMF) Compliance Map

**System**: Engram (Context Engineering Platform)
**Level**: AI RMF 1.0
**Target Profile**: Generative AI (LLM) Risk Profile

## Executive Summary

This document maps Engram's security and governance controls to the NIST AI RMF 1.0 Core functions: **GOVERN**, **MAP**, **MEASURE**, and **MANAGE**.

Current Focus: **Identity & Access Management (IAM)** and **Memory Integrity**.

---

## 1. GOVERN

*Cultivate a culture of risk management.*

| Function ID | Description | Engram Control | Status |
|:---:|:---|:---|:---:|
| **GOVERN 1.1** | Policies and procedures in place. | `docs/operations/business-plan.md` defines roles. | ✅ Partial |
| **GOVERN 1.2** | Accountability establishes. | Roles: Elena (GTM), Marcus (PM), Sage (Tech). | ✅ Implemented |
| **GOVERN 1.3** | Workforce diversity/accessibility. | N/A for Agent workforce currently. | ⚪ N/A |

## 2. MAP

*Context is recognized and risks are identified.*

| Function ID | Description | Engram Control | Status |
|:---:|:---|:---|:---:|
| **MAP 1.1** | System Context understood. | `docs/architecture/index.md` + Self-Enriching Workflow. | ✅ Implemented |
| **MAP 1.5** | Risks to security identified. | **Risk**: Unrestricted API Key access to Memory. <br> **Mitigation**: Move to Managed Identity. | ⚠️ Identified |
| **MAP 1.6** | Risks to privacy identified. | **Risk**: PII in Zep Memory. <br> **Mitigation**: Zep PII Scrubbing (Feature). | ⚠️ Tracking |

## 3. MEASURE

*Risks are assessed, analyzed, and tracked.*

| Function ID | Description | Engram Control | Status |
|:---:|:---|:---|:---:|
| **MEASURE 1.1** | Appropriate methods used. | Automated tests (`pytest`), Verification Scripts. | ✅ Implemented |
| **MEASURE 2.2** | Performance measured. | Temporal UI metrics, Azure Monitor. | ✅ Implemented |
| **MEASURE 2.6** | Fairness/Bias testing. | Not currently testing for output bias. | 🔴 Gap |

## 4. MANAGE

*Risks are prioritized and acted upon.*

| Function ID | Description | Engram Control | Status |
|:---:|:---|:---|:---:|
| **MANAGE 1.3** | Response to new risks. | Agile task tracking in `task.md`. | ✅ Implemented |
| **MANAGE 2.4** | Incident response. | Azure Alerts -> Temporal Retry Policy. | ✅ Partial |
| **MANAGE 4.1** | **Access Control** | **Current**: `X-API-Key` (Public Endpoint). <br> **Target**: Azure Managed Identity (App-to-App). | ⚠️ **ACTION REQUIRED** |

---

## Roadmap to "Lock Down"

### Phase 1: Authentication Hardening (Immediate)

- [ ] **Deprecate API Keys**: Remove `verify_api_key` simple string check.
- [ ] **Implement OIDC**: Use Microsoft Entra ID (OIDC) for all Agent-to-API calls.
- [ ] **Service Principals**: Assign specific Service Principals to external agents (Cursor, Windsurf).

### Phase 2: Memory RBAC

- [ ] **Role Definition**: Define `Memory.Read`, `Memory.Write`, `Memory.Admin` roles in App Registration.
- [ ] **Enforcement**: Update `routers/memory.py` to check `roles` claim in JWT.

### Phase 3: Network Security

- [ ] **Private Endpoint**: Move Zep and Postgres to VNET-only access (disable public IP).
- [ ] **WAF**: Enable Azure Front Door WAF for public API entry points.
