# NIST SP 800-161 Supply Chain Risk Management

**Engram AI Platform — Supply Chain Security Compliance**

> [!NOTE]
> This document maps Engram's supply chain security controls to NIST SP 800-161 Rev. 1:  
> *Cybersecurity Supply Chain Risk Management Practices for Systems and Organizations*

---

## Overview

Engram implements continuous supply chain security through automated SBOM (Software Bill of Materials) generation and vulnerability scanning integrated into the CI/CD pipeline.

| Tool | Purpose | Standard |
|------|---------|----------|
| **Syft** (Anchore) | SBOM Generation | SPDX 2.3 / CycloneDX |
| **Grype** (Anchore) | Vulnerability Scanning | CVE/NVD/GHSA |

---

## Control Mapping

### SR-3: Supply Chain Risk Assessment

**Requirement:** Assess and document supply chain risks associated with development and acquisition.

**Implementation:**

- Automated vulnerability scanning (Grype) on every container image build
- Severity thresholds: **HIGH** and **CRITICAL** vulnerabilities fail the build
- SARIF reports uploaded to GitHub Security tab for centralized visibility
- Historical vulnerability trends tracked via GitHub Security Advisories

**Evidence:**

- CI Workflow: `.github/workflows/ci.yml` → `security-scan` job
- GitHub Security → Code Scanning Alerts

---

### SR-4: Provenance

**Requirement:** Employ tools and techniques to document and verify provenance of acquired components.

**Implementation:**

- SBOM generation for all container images (SPDX JSON format)
- SBOMs include:
  - Package names, versions, and licenses
  - Dependency relationships
  - Cryptographic checksums (SHA256)
- SBOMs uploaded as build artifacts for audit trail

**Evidence:**

- Build Artifacts: `sbom-backend.spdx.json`, `sbom-worker.spdx.json`
- SPDX format enables interoperability with NTIA minimum elements

---

### SR-5: Acquisition Strategies, Tools, and Methods

**Requirement:** Use acquisition strategies that ensure supply chain security.

**Implementation:**

- Container images built from verified base images (`python:3.11-slim`)
- Dependencies pinned via `requirements.txt` with integrity verification
- GitHub Dependabot monitors for known vulnerabilities
- Private container registry (GHCR) with access controls

**Evidence:**

- `backend/Dockerfile` — base image specification
- `backend/requirements.txt` — pinned dependencies
- GitHub → Dependabot Alerts

---

### SR-6: Supplier Assessments

**Requirement:** Assess suppliers of critical system components.

**Implementation:**

- Third-party services vetted for enterprise compliance:
  - **Zep** (Memory): SOC 2 Type II
  - **Azure** (Infrastructure): FedRAMP High
  - **Google Cloud** (AI Models): ISO 27001
- Open-source dependencies scanned against OSSF Scorecard (planned)

**Evidence:**

- Vendor security documentation in `docs/03-operations/vendor-security/`

---

### SR-8: Notification Agreements

**Requirement:** Establish agreements for notification of supply chain compromises.

**Implementation:**

- GitHub Security Advisories enabled for repository
- Dependabot alerts configured for automatic notification
- Slack integration for CI/CD failure notifications (including security scan failures)

**Evidence:**

- Repository Settings → Security → Advisories
- `.github/workflows/ci.yml` → Slack notification on failure

---

## SBOM Standard Compliance

Engram SBOMs conform to:

| Standard | Compliance |
|----------|------------|
| **NTIA Minimum Elements** | ✅ All 7 elements included |
| **SPDX 2.3** | ✅ Primary format |
| **CycloneDX 1.4** | ✅ Available via Syft |
| **Executive Order 14028** | ✅ Meets federal SBOM requirements |

### NTIA Minimum Elements Checklist

- [x] Supplier Name
- [x] Component Name
- [x] Version String
- [x] Unique Identifiers (PURL)
- [x] Dependency Relationships
- [x] Author of SBOM Data
- [x] Timestamp

---

## Vulnerability Management Policy

### Severity Response

| Severity | Response Time | Build Gate |
|----------|--------------|------------|
| **Critical** | 24 hours | ❌ Blocks deployment |
| **High** | 72 hours | ❌ Blocks deployment |
| **Medium** | 14 days | ⚠️ Warning only |
| **Low** | 30 days | ℹ️ Informational |

### Suppression Process

Known false positives or accepted risks can be suppressed via:

1. `.grype.yaml` configuration file
2. GitHub Code Scanning → Dismiss Alert (with justification)

All suppressions require documented justification and periodic review (quarterly).

---

## Audit Evidence

For compliance audits, the following evidence is available:

| Artifact | Location | Retention |
|----------|----------|-----------|
| SBOM Files | GitHub Actions Artifacts | 90 days |
| Vulnerability Scans | GitHub Security Tab | Indefinite |
| Build Logs | GitHub Actions | 90 days |
| Dependency Updates | GitHub Dependabot History | Indefinite |

---

## References

- [NIST SP 800-161 Rev. 1](https://csrc.nist.gov/publications/detail/sp/800-161/rev-1/final)
- [Executive Order 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/)
- [NTIA SBOM Minimum Elements](https://www.ntia.gov/report/2021/minimum-elements-software-bill-materials-sbom)
- [SPDX Specification](https://spdx.dev/specifications/)
- [Anchore Syft](https://github.com/anchore/syft)
- [Anchore Grype](https://github.com/anchore/grype)

---

*Document Version: 1.0*  
*Last Updated: 2026-01-10*  
*Owner: Zimax Networks LC*
