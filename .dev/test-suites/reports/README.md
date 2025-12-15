# Test Reports

This directory contains test execution reports and results. Reports are gitignored to keep the repository clean.

## Report Types

### Test Execution Reports
- Unit test results
- Integration test results
- E2E test results
- Coverage reports

### Performance Reports
- Load test results
- Response time metrics
- Resource utilization

### Staging Test Reports
- Environment validation results
- Production readiness checks
- Deployment verification

## Naming Convention

Use the format: `YYYY-MM-DD_test-type_result.{html|json|xml}`

Examples:
- `2025-12-15_unit_coverage.html`
- `2025-12-15_e2e_playwright-report.html`
- `2025-12-15_staging_validation.json`

## Viewing Reports

Most test frameworks generate HTML reports that can be opened in a browser:

```bash
# Playwright report
npx playwright show-report .dev/test-suites/reports/playwright-report

# Python coverage report
open .dev/test-suites/reports/htmlcov/index.html
```

## Cleanup

Reports older than 30 days should be archived or deleted to keep this directory clean.
