# Code Review Security Roadmap — 2026

**"Whoever owns review and merge effectively owns organizational trust"**

Security is becoming a primitive for user experience. As AI agents generate more code, the human approval gate becomes the critical security boundary.

---

## Current State (Q1 2026)

| Capability | Status |
|------------|--------|
| DCO Check | ✅ Implemented |
| SBOM Generation (Syft) | ✅ Implemented |
| Vulnerability Scanning (Grype) | ✅ Implemented |
| Structured Audit Logging | 🚧 Partial |
| Memory Provenance | ✅ Core feature |

---

## Roadmap Items

### Phase 1: Foundation (Q1 2026)

#### 1.1 Approval Gates

- [ ] Add `CODEOWNERS` for sensitive paths:
  - `/backend/api/middleware/auth.py`
  - `/backend/core/database.py`
  - `/infra/*.bicep`
- [ ] Configure branch protection with required reviewers
- [ ] Add Temporal workflow for agent action approval

#### 1.2 Policy Checks

- [ ] Create `.pre-commit-config.yaml` with:
  - Ruff (Python linting)
  - ESLint (TypeScript)
  - Secrets detection (detect-secrets)
- [ ] Add custom policy rules for security patterns

#### 1.3 Comprehensive Logs

- [ ] Extend `backend/core/audit.py`:
  - AUTH_FAILURE events
  - SENSITIVE_ACCESS events
  - RETRIEVAL_EVENT with provenance
- [ ] Forward to Azure Monitor / Log Analytics

---

### Phase 2: Risk Management (Q2 2026)

#### 2.1 Risk Scoring

- [ ] Create `scripts/risk_score.py`:
  - Lines changed (>400 = high risk)
  - File sensitivity weighting
  - AI-generated code flag
  - Historical defect rate lookup
- [ ] Add risk score to PR template

#### 2.2 Constrained Execution

- [ ] Define `agent_constraints` config:
  - Allowed file paths per agent
  - Rate limits (tokens/requests per hour)
  - Sandbox execution environment
- [ ] Implement constraint enforcement in agent executor

#### 2.3 Rollback Capabilities

- [ ] Create `scripts/rollback.sh`:
  - Git revert helper
  - Container Apps revision rollback
  - Database migration rollback (Alembic)
- [ ] Document rollback procedures in runbook

---

### Phase 3: AI Review Integration (Q2-Q3 2026)

#### 3.1 AI Code Review

- [ ] Evaluate OSS options:
  - **Qodo Merge** (PR-Agent) — OSS, self-hostable
  - **CodeRabbit** — SaaS alternative
  - Native GitHub + Copilot
- [ ] Implement selected solution
- [ ] Add custom rules for Engram patterns

#### 3.2 Test Synthesis

- [ ] Agent workflow for generating unit tests
- [ ] Property-based testing with Hypothesis
- [ ] Mutation testing with mutmut

#### 3.3 Feature Flags

- [ ] Evaluate: Unleash (OSS) vs LaunchDarkly
- [ ] Implement feature flag system
- [ ] Enable gradual rollouts for risky changes

---

## Research: Graphite

| Question | Finding |
|----------|---------|
| Open Source? | ❌ No — Commercial SaaS only |
| Self-Hosted? | ❌ No — Cloud only |
| Status | Acquired by Cursor (Dec 2025) |

**Key Features:**

- Diamond AI reviewer (<3% false positive)
- Stacked PRs for manageable reviews
- Merge queue automation
- Custom policy checks

**Recommendation:** Use **Qodo Merge** (OSS) or GitHub native + custom tooling.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| PR Review Time | <4 hours for standard PRs |
| Security Scan Pass Rate | >95% first-pass |
| Rollback Time | <15 minutes |
| Audit Log Coverage | 100% of security events |
| False Positive Rate | <5% for policy checks |

---

## References

- NIST 800-161: Supply Chain Risk Management
- [DCO Sign-Off](https://developercertificate.org/)
- [Qodo Merge](https://github.com/Codium-ai/pr-agent)
- [Engram Security Implementation Plan](../security/security-implementation-plan.md)
- [NIST 800-161 Compliance](../security/nist-800-161-compliance.md)

---

*Created: 2026-01-10*  
*Owner: Zimax Networks LC*
