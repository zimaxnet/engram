# Vendor Documentation & Release Monitoring

## Overview

Since Engram uses self-hosted components (Zep, Temporal, Unstructured) without enterprise support contracts, we must **actively monitor vendor documentation and release notes** to stay current with security patches, features, and breaking changes.

## Monitored Vendors

| Vendor | Component | Documentation Site | Release Notes | RSS/Atom Feed |
|--------|-----------|-------------------|---------------|---------------|
| **Zep** | Memory/KG | https://docs.getzep.com | GitHub Releases | https://github.com/getzep/zep/releases.atom |
| **Temporal** | Workflow Engine | https://docs.temporal.io | GitHub Releases | https://github.com/temporalio/temporal/releases.atom |
| **Unstructured** | Document Processing | https://docs.unstructured.io | GitHub Releases | https://github.com/Unstructured-IO/unstructured/releases.atom |
| **FastAPI** | Backend Framework | https://fastapi.tiangolo.com | GitHub Releases | https://github.com/tiangolo/fastapi/releases.atom |
| **LangSmith** | Observability (optional) | https://docs.smith.langchain.com | Changelog | - |

## Monitoring Checklist

### Weekly Review

- [ ] Check Zep releases (GitHub) for security patches
- [ ] Check Temporal releases for breaking changes
- [ ] Check Unstructured releases for new connectors/features
- [ ] Review FastAPI releases for security updates
- [ ] Scan vendor docs for new configuration options

### Monthly Review

- [ ] Review Zep changelog for major version bumps
- [ ] Review Temporal upgrade guides (if version change planned)
- [ ] Review Unstructured connector roadmap
- [ ] Check for deprecated features/APIs in vendor docs
- [ ] Update Engram dependencies if security patches available

### Per-Release Review

Before upgrading any vendor component:

- [ ] Read release notes (breaking changes, security fixes)
- [ ] Review migration guides (if major version bump)
- [ ] Test in dev environment first
- [ ] Update Engram code/config if APIs changed
- [ ] Update documentation (this file, deployment guides)

## Automated Monitoring (Future)

### CI/CD Integration

Add a non-blocking job to CI that:
1. Checks latest release tags from vendor GitHub repos
2. Compares to `requirements.txt` / `docker-compose.yml` versions
3. Logs warning if newer versions available (don't block deployment)
4. Creates GitHub issue if security patch available

Example script:
```bash
#!/bin/bash
# scripts/check-vendor-updates.sh

ZEP_LATEST=$(curl -s https://api.github.com/repos/getzep/zep/releases/latest | jq -r .tag_name)
ZEP_CURRENT=$(grep "getzep/zep" docker-compose.yml | grep -oP ':\K[^:]+')

if [ "$ZEP_LATEST" != "$ZEP_CURRENT" ]; then
  echo "⚠️  Zep update available: $ZEP_CURRENT → $ZEP_LATEST"
fi
```

### RSS Feed Monitoring

Use GitHub Actions or scheduled job to:
- Subscribe to vendor release RSS feeds
- Parse releases for security keywords ("security", "CVE", "vulnerability")
- Create GitHub issues for critical security patches

## Version Pinning Strategy

### Docker Images

Pin to specific tags (not `latest`) for reproducibility:
```yaml
# docker-compose.yml
zep:
  image: getzep/zep:v0.45.2  # Pinned version

temporal:
  image: temporalio/auto-setup:1.23.0  # Pinned version
```

### Python Dependencies

Pin to specific versions in `requirements.txt`:
```
zep-python==2.0.0
temporalio==1.5.0
unstructured[all-docs]==0.15.0
fastapi==0.115.0
```

## Security Patch Response

### Critical (CVE with exploit)

1. **Immediate**: Review CVE details, assess impact on Engram
2. **Within 24h**: Test patch in dev, deploy to staging
3. **Within 48h**: Deploy to production (if staging tests pass)

### High (Security issue, no known exploit)

1. **Within 1 week**: Test patch, plan deployment
2. **Within 2 weeks**: Deploy to staging, then production

### Medium/Low

1. **Include in next scheduled upgrade**: Test with other changes, deploy during maintenance window

## Breaking Changes

### Pre-Release Detection

Monitor vendor release notes for:
- API changes (method signatures, response formats)
- Configuration changes (env vars, config files)
- Database schema changes (Zep, Temporal)
- Dependency updates (Python, Node versions)

### Migration Process

1. **Review migration guide** (vendor docs)
2. **Update Engram code** to match new APIs
3. **Update tests** to match new behavior
4. **Test in dev** environment
5. **Deploy to staging** for validation
6. **Deploy to production** after staging validation

## Documentation Updates

When vendors release updates:

- [ ] Update Engram documentation (deployment guides, architecture docs)
- [ ] Update `CHANGELOG.md` with vendor updates
- [ ] Update this monitoring checklist if process changes

## Escalation

If a vendor issue blocks Engram:

1. **Check vendor GitHub issues**: Search for similar problems
2. **Check vendor Discord/Slack**: Community support
3. **Review vendor docs**: May have workarounds
4. **Consider fork/contribution**: If open-source, can contribute fix
5. **Evaluate alternatives**: If vendor is unresponsive, consider alternatives (long-term)

## Vendor-Specific Notes

### Zep

- **Release cadence**: ~monthly minor releases, quarterly major releases
- **Breaking changes**: Usually documented in migration guides
- **Database migrations**: Run via Zep's auto-migration (set `ZEP_ENABLE_AUTOMIGRATION=true`)

### Temporal

- **Release cadence**: Monthly minor, ~quarterly major
- **Breaking changes**: Well-documented in upgrade guides
- **Database schema**: Temporal handles migrations automatically (via `auto-setup` image)

### Unstructured

- **Release cadence**: Frequent (weekly/bi-weekly)
- **Breaking changes**: Usually backward-compatible
- **New connectors**: Added frequently; check release notes for new source types

### FastAPI

- **Release cadence**: ~monthly
- **Breaking changes**: Rare (major version bumps only)
- **Security**: Pydantic (dependency) occasionally has security patches

## Review Log

Keep a log of vendor updates reviewed:

| Date | Vendor | Component | Version | Notes | Status |
|------|--------|-----------|---------|-------|--------|
| 2025-12-13 | Zep | Memory | v0.45.2 | Current pinned version | ✅ |
| 2025-12-13 | Temporal | Workflow | 1.23.0 | Current pinned version | ✅ |
