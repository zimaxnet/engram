# Test Suites Working Directory

This directory contains all test suite files organized by type. All test development, execution, and reporting should be done from this location.

## Directory Structure

```
test-suites/
├── unit/          # Unit test files (backend Python tests)
├── integration/   # Integration test files
├── e2e/          # End-to-end Playwright test files
├── staging/      # Staging environment specific tests
├── reports/      # Test execution reports and results
└── README.md     # This file
```

## Test Categories

### Unit Tests (`unit/`)
- Backend API route tests
- Service layer tests
- Utility function tests
- Database model tests

**Examples:**
- `test_admin_router.py`
- `test_memory_router.py`
- `test_workflows_router.py`

### Integration Tests (`integration/`)
- Multi-service integration tests
- Database integration tests
- External API integration tests
- Workflow integration tests

### E2E Tests (`e2e/`)
- Full user flow tests (Playwright)
- UI interaction tests
- Cross-browser compatibility tests

**Examples:**
- `bau-flow.spec.ts`
- `evidence-drill.spec.ts`
- `golden-thread.spec.ts`
- `voice-interaction.spec.ts`
- `workflow-signal.spec.ts`

### Staging Tests (`staging/`)
- Environment-specific tests
- Production readiness tests
- Performance tests
- Load tests

### Reports (`reports/`)
- Test execution reports
- Coverage reports
- Performance metrics
- Test result summaries

## Running Tests

### Unit Tests (Python)
```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
python -m pytest .dev/test-suites/unit/ -v
```

### E2E Tests (Playwright)
```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
npx playwright test .dev/test-suites/e2e/
```

### All Tests
```bash
# Run all test suites
./scripts/run-all-tests.sh
```

## Test Development Guidelines

1. **Naming Convention**
   - Unit tests: `test_*.py`
   - E2E tests: `*.spec.ts`
   - Integration tests: `test_*_integration.py`

2. **Organization**
   - Keep tests in appropriate category folders
   - Mirror source code structure where applicable
   - Group related tests together

3. **Documentation**
   - Add descriptive docstrings to test functions
   - Document test setup requirements
   - Include comments for complex test logic

4. **Cleanup**
   - Remove obsolete tests
   - Archive old test reports
   - Keep directory structure clean

## Current Test Inventory

### Backend Unit Tests (Python)
- ✓ Admin router tests
- ✓ Memory router tests  
- ✓ Workflows router tests

### Frontend E2E Tests (Playwright)
- ✓ BAU flow tests
- ✓ Evidence drill tests
- ✓ Golden thread tests
- ✓ Voice interaction tests
- ✓ Workflow signal tests

## Next Steps

- [ ] Copy existing tests to appropriate directories
- [ ] Set up test configuration files
- [ ] Create test utilities and fixtures
- [ ] Configure CI/CD pipeline integration
- [ ] Set up automated test reporting
