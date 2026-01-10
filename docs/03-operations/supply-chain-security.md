# Supply Chain Security Operations

**Runbook for SBOM Generation and Vulnerability Scanning**

---

## Quick Reference

```bash
# Install tools (macOS)
brew install syft grype

# Generate SBOM
syft <image> -o spdx-json > sbom.json

# Scan for vulnerabilities  
grype <image> --output table
```

---

## Local SBOM Generation

### Container Images

```bash
# Backend image
syft ghcr.io/zimax-net/engram/backend:latest -o spdx-json > sbom-backend.spdx.json

# Worker image
syft ghcr.io/zimax-net/engram/worker:latest -o spdx-json > sbom-worker.spdx.json
```

### Source Directory

```bash
# Scan Python dependencies from requirements.txt
syft dir:backend/ -o spdx-json > sbom-source.spdx.json
```

### Output Formats

| Format | Use Case | Command |
|--------|----------|---------|
| SPDX JSON | Compliance/Audit | `-o spdx-json` |
| CycloneDX | Integration | `-o cyclonedx-json` |
| Table | Human review | `-o table` |

---

## Vulnerability Scanning

### Scan Container Image

```bash
# Quick scan with table output
grype ghcr.io/zimax-net/engram/backend:latest

# Detailed JSON output
grype ghcr.io/zimax-net/engram/backend:latest -o json > vulns.json

# Filter by severity
grype ghcr.io/zimax-net/engram/backend:latest --fail-on high
```

### Scan from SBOM

```bash
# More accurate - uses SBOM as source of truth
grype sbom:sbom-backend.spdx.json
```

### Understanding Output

```
NAME              INSTALLED  FIXED-IN  TYPE    VULNERABILITY   SEVERITY
cryptography      41.0.0     41.0.4    python  CVE-2023-xxxx   High
requests          2.28.0     2.31.0    python  CVE-2023-yyyy   Medium
```

- **INSTALLED**: Current version in your image
- **FIXED-IN**: Version that patches the vulnerability
- **TYPE**: Package ecosystem (python, npm, os)
- **SEVERITY**: Critical > High > Medium > Low > Negligible

---

## Remediation Procedures

### 1. Identify Affected Package

```bash
# Find where package is defined
grep -r "cryptography" backend/requirements.txt
```

### 2. Check Fixed Version

```bash
# View CVE details
grype db search CVE-2023-xxxx
```

### 3. Update Dependency

```bash
# Update requirements.txt
# cryptography==41.0.0  →  cryptography==41.0.4

# Rebuild and verify
docker build -t test-backend ./backend
grype test-backend --fail-on high
```

### 4. Suppress False Positives

Create `.grype.yaml` in repository root:

```yaml
ignore:
  - vulnerability: CVE-2023-xxxxx
    reason: "False positive - not exploitable in our context"
    expires: "2026-04-10"  # Requires re-review
```

---

## CI/CD Integration

The security scan runs automatically in CI after Docker images are built:

```
CI Workflow → build-images → security-scan
                              ├── SBOM Generation (Syft)
                              └── Vulnerability Scan (Grype)
```

### Build Gates

| Severity | Action |
|----------|--------|
| Critical/High | ❌ Build fails |
| Medium/Low | ⚠️ Warning only |

### Viewing Results

1. **GitHub Actions** → Select workflow run → `security-scan` job
2. **GitHub Security** → Code scanning → View all alerts
3. **Artifacts** → Download SBOM files

---

## Scheduled Scans

For continuous monitoring, run weekly scans:

```bash
# Cron job example
0 0 * * 0 /usr/local/bin/grype ghcr.io/zimax-net/engram/backend:latest \
  --output json | /usr/local/bin/notify-vulnerabilities.sh
```

---

## Database Updates

Grype uses a local vulnerability database that should be updated regularly:

```bash
# Update database
grype db update

# Check database status
grype db status
```

---

## Compliance Reporting

### Generate Audit Report

```bash
# Full SBOM + vulnerability report
syft ghcr.io/zimax-net/engram/backend:latest -o spdx-json > sbom.json
grype sbom:sbom.json -o json > vulnerabilities.json

# Combine into audit package
tar -czf audit-report-$(date +%Y%m%d).tar.gz sbom.json vulnerabilities.json
```

### NIST 800-161 Evidence

See [nist-800-161-compliance.md](../security/nist-800-161-compliance.md) for control mapping.

---

*Last Updated: 2026-01-10*
