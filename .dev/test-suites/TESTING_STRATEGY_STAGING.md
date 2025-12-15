# Testing Strategy: Staging Environment Only

**Effective Date**: December 15, 2025  
**Environment**: Staging Only  
**Status**: Active

---

## Overview

All tests are configured to run **exclusively against the STAGING environment**. This policy ensures:

1. ✅ No accidental test execution against development, UAT, or production
2. ✅ Consistent test environment across all developers
3. ✅ Safety from data loss or contamination
4. ✅ Staging servers configured specifically for testing needs

---

## Environment Configuration

### Available Environments
```
Production (prod)   - Live customer data [DO NOT TEST]
UAT (uat)          - User acceptance testing [DO NOT TEST]
Test (test)        - Legacy test environment [DEPRECATED]
Dev (dev)          - Developer sandboxes [DO NOT TEST]
Staging (staging)  - Dedicated testing environment [TESTS ONLY ✓]
```

### Staging Environment Details
```
Environment:  staging
Vault:        engram-staging-vault
Vault URL:    https://engram-staging-vault.vault.azure.net/
AI Endpoint:  (from environment)
AI Key:       (from environment)
```

---

## Test Configuration

### How Tests Enforce Staging

1. **Global conftest.py** (`backend/tests/conftest.py`)
   - Automatically sets ENVIRONMENT=staging
   - Verifies environment at pytest_sessionstart
   - Enforces staging on all tests via autouse fixture
   - Adds @pytest.mark.staging to every test

2. **Test File Setup**
   - Each test file sets environment variables at import time
   - conftest.py overrides to ensure staging
   - Environment check fixture validates before each test

3. **pytest.ini Configuration**
   - Specifies staging as default environment
   - Defines staging markers
   - Blocks production markers from running

### Test Files with Staging Configuration

✅ `test_chat_router.py` - Chat endpoint tests  
✅ `test_memory_router_expanded.py` - Memory search edge cases  
✅ `test_memory_operations.py` - Memory enrichment & persistence  
✅ `test_memory_router_contracts.py` - Memory contracts (updated)  

---

## Running Tests

### Default: All Tests (Staging Only)
```bash
cd backend
pytest tests/
```

### Run Specific Test Class
```bash
pytest tests/test_chat_router.py::TestChatEndpoint -v
```

### Run Single Test
```bash
pytest tests/test_chat_router.py::TestChatEndpoint::test_send_message_basic -v
```

### View Environment Information
```bash
pytest tests/ -v -s --capture=no
# Look for: "PYTEST CONFIGURATION: Staging Environment Tests"
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=backend --cov-report=html
```

---

## Safety Guarantees

### ✅ Automatic Protections

1. **Environment Lock-in**
   ```python
   # conftest.py enforces this on every test
   assert os.environ.get("ENVIRONMENT") == "staging"
   ```

2. **Session-Level Verification**
   ```python
   # Checked before ANY tests run
   if environment != "staging":
       raise RuntimeError("Tests must run against STAGING only!")
   ```

3. **Per-Test Validation**
   ```python
   # All tests have autouse fixture
   @pytest.fixture(autouse=True)
   def ensure_staging_env(environment_check):
       assert os.environ.get("ENVIRONMENT") == "staging"
       yield
   ```

### ❌ What Cannot Happen

- ❌ Tests running against production
- ❌ Tests running against UAT without explicit approval
- ❌ Tests running against dev without developer warning
- ❌ Environment bypass without code review

---

## Test Markers

All tests are automatically marked with `@pytest.mark.staging`:

```bash
# Run only staging tests (all tests)
pytest tests/ -m staging

# View all staging tests
pytest tests/ -m staging --collect-only

# Run tests excluding production (same as above, since all are staging)
pytest tests/ -m "not production"
```

---

## Adding New Tests

When creating new test files:

1. **Set environment at top of file**:
   ```python
   import os
   os.environ.setdefault("ENVIRONMENT", "staging")
   os.environ.setdefault("AZURE_KEY_VAULT_NAME", "engram-staging-vault")
   ```

2. **conftest.py will automatically**:
   - Override to ensure staging
   - Add @pytest.mark.staging
   - Validate environment

3. **Example new test**:
   ```python
   # backend/tests/test_workflows_router.py
   import os
   os.environ.setdefault("ENVIRONMENT", "staging")
   os.environ.setdefault("AZURE_KEY_VAULT_NAME", "engram-staging-vault")
   
   import pytest
   from fastapi.testclient import TestClient
   from backend.api.main import create_app
   
   @pytest.fixture
   def client():
       app = create_app()
       return TestClient(app)
   
   class TestWorkflowEndpoints:
       def test_list_workflows(self, client):
           response = client.get("/api/v1/workflows")
           assert response.status_code in [200, 401]
   ```

---

## CI/CD Pipeline Integration

### GitHub Actions / Azure Pipelines

```yaml
test:
  runs-on: ubuntu-latest
  env:
    ENVIRONMENT: staging  # Always staging
    AZURE_KEY_VAULT_NAME: engram-staging-vault
  steps:
    - uses: actions/checkout@v3
    - run: pip install -r requirements.txt
    - run: pytest backend/tests/ -v
      # Will fail automatically if ENVIRONMENT != staging
```

---

## Staging Server Requirements

Staging servers are configured with:

✅ Full Engram platform deployment  
✅ Test data seeded for consistency  
✅ API rate limits disabled for testing  
✅ Verbose logging enabled  
✅ Memory services (Zep) configured  
✅ Temporal workflow engine ready  
✅ LLM integrations mocked (or test keys)  

---

## Troubleshooting

### Issue: Tests fail with environment error

```
RuntimeError: Tests must run against STAGING environment only!
Current environment: production
```

**Solution**: 
```bash
# Ensure ENVIRONMENT is not set in shell
unset ENVIRONMENT
unset AZURE_KEY_VAULT_NAME

# Run tests (conftest will set staging)
pytest tests/
```

### Issue: Tests running against wrong vault

**Cause**: AZURE_KEY_VAULT_NAME environment variable is persisting  

**Solution**:
```bash
# Clear environment
env -i bash
cd /path/to/engram

# Run pytest (starts clean)
pytest backend/tests/ -v
```

### Issue: conftest.py not loading

**Cause**: conftest.py file not in tests/ directory  

**Solution**:
```bash
# Verify file exists
ls -la backend/tests/conftest.py

# Should see: backend/tests/conftest.py (created Dec 15, 2025)
```

---

## Staging vs Other Environments

| Aspect | Staging | UAT | Prod | Dev |
|--------|---------|-----|------|-----|
| **Testing** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Data Risk** | Low (test data only) | High | Critical | Medium |
| **Deployment Frequency** | On-demand | Weekly | Monthly | Continuous |
| **Test Data Reset** | Daily | Never | Never | Per-developer |
| **LLM Costs** | Minimized (mocked) | Minimized | Full | Minimized |

---

## Approval Process

### If Tests Need to Run Against UAT

Requires:
1. ✅ Technical Lead approval
2. ✅ UAT stakeholder sign-off
3. ✅ Documented reason in PR
4. ✅ Code review with explicit @pytest.mark.uat

### If Tests Need Production Data

**NOT ALLOWED** - Use staging replicated data instead

---

## Test Coverage by Phase

### Phase 1: Chat & Memory (Current)
- ✅ test_chat_router.py - 17 tests
- ✅ test_memory_router_expanded.py - 25+ tests
- ✅ test_memory_operations.py - 20+ tests
- **Total**: 62+ tests on staging

### Phase 2: Workflows & Agents (Coming)
- test_workflows_router.py - ~30 tests (staging only)
- test_agents_router.py - ~20 tests (staging only)
- test_agent_tools.py - ~15 tests (staging only)

### Phase 3: Frontend Services (Coming)
- test_api_client.py - ~25 tests (staging only)
- test_service_wrappers.py - ~20 tests (staging only)

**All tests: Staging environment only**

---

## Success Criteria

✅ All Phase 1 tests passing on staging  
✅ No environment variable leakage to other envs  
✅ CI/CD enforces staging environment  
✅ New tests require explicit staging configuration  
✅ Team trained on staging-only policy  

---

## Contact & Questions

For environment or testing questions:
- **Testing Lead**: Review conftest.py
- **DevOps**: Verify staging infrastructure
- **Code Review**: Enforce staging markers on all PRs

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| Dec 15, 2025 | 1.0 | Initial staging-only testing strategy |

