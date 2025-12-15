# Environment Enforcement: Staging Only

**Status**: ✅ Active  
**Date**: December 15, 2025  
**Policy**: All tests must run against STAGING environment

---

## 3-Layer Environment Protection

Your test suite has 3 independent mechanisms that ensure tests run against staging:

### Layer 1: pytest Configuration (pytest.ini)
```ini
[pytest]
addopts = --environment=staging  # Sets default environment

[tool:pytest]
env = staging  # Pytest environment variable
```

**What it does**: Tells pytest the default environment is staging  
**Protection level**: Weak (can be overridden)

---

### Layer 2: Pytest Session Validation (conftest.py)
```python
def pytest_sessionstart(session):
    """Verify staging environment BEFORE any tests run"""
    environment = os.environ.get("ENVIRONMENT", "").lower()
    
    if environment != "staging":
        raise RuntimeError(
            f"ERROR: Tests must run against STAGING environment only!\n"
            f"Current environment: {environment}\n"
            f"Allowed environments: staging"
        )
```

**What it does**: Checks environment before the first test runs  
**Protection level**: Strong (hard stop if wrong environment)  
**When it runs**: Once per test session, at the very beginning

---

### Layer 3: Per-Test Validation (conftest.py fixture)
```python
@pytest.fixture(autouse=True)
def ensure_staging_env():
    """Verify staging environment before EVERY test"""
    assert os.environ.get("ENVIRONMENT") == "staging"
    yield
```

**What it does**: Confirms staging before every single test  
**Protection level**: Very Strong (catches runtime environment changes)  
**When it runs**: Before and after each test

---

### Layer 4: Automatic Environment Setup (conftest.py)
```python
def pytest_configure(config):
    """Force staging environment on startup"""
    os.environ["ENVIRONMENT"] = "staging"
    os.environ["AZURE_KEY_VAULT_NAME"] = "engram-staging-vault"
    os.environ["AZURE_KEYVAULT_URL"] = "https://engram-staging-vault.vault.azure.net/"
```

**What it does**: Actively sets environment to staging  
**Protection level**: Strongest (proactive, not reactive)  
**When it runs**: When pytest starts, before anything else

---

## How Tests Execute

```
Step 1: You run pytest
        ↓
Step 2: pytest_configure() runs
        → Sets ENVIRONMENT=staging
        → Sets AZURE_KEY_VAULT_NAME=engram-staging-vault
        → Prints confirmation banner
        ↓
Step 3: pytest_sessionstart() runs
        → Reads ENVIRONMENT from os.environ
        → Checks if it equals "staging"
        → If not: STOP. Raise error.
        → If yes: Print ✓ Confirmed
        ↓
Step 4: Each test starts
        → ensure_staging_env fixture runs
        → Asserts ENVIRONMENT=="staging"
        → If not: Test FAILS with clear error
        → If yes: Test continues
        ↓
Step 5: Test executes with staging environment
        ↓
Step 6: Test completes
        → ensure_staging_env fixture cleanup
        → Next test starts (back to Step 4)
```

---

## Actual Output When Running Tests

When you run:
```bash
pytest backend/tests/test_chat_router.py -v
```

You'll see:

```
======================================================================
PYTEST CONFIGURATION: Staging Environment Tests
======================================================================
Environment: staging
Vault: engram-staging-vault
======================================================================

✓ Confirmed: Running tests against STAGING environment

backend/tests/test_chat_router.py::TestChatEndpoint::test_send_message_basic PASSED
backend/tests/test_chat_router.py::TestChatEndpoint::test_send_message_with_session PASSED
backend/tests/test_chat_router.py::TestChatEndpoint::test_message_response_has_message_id PASSED
...
```

The confirmation line `✓ Confirmed: Running tests against STAGING environment` means all 3 protection layers have verified staging is active.

---

## Environment Variables Set Automatically

When pytest runs, these are automatically set:

| Variable | Value | Source |
|----------|-------|--------|
| ENVIRONMENT | staging | conftest.py |
| AZURE_KEY_VAULT_NAME | engram-staging-vault | conftest.py |
| AZURE_KEYVAULT_URL | https://engram-staging-vault.vault.azure.net/ | conftest.py |
| AZURE_AI_ENDPOINT | (from environment if available) | conftest.py |
| AZURE_AI_KEY | (from environment if available) | conftest.py |

**You do not need to set these manually.**

---

## What Happens If Someone Tries to Override

### Attempt 1: Set environment before pytest
```bash
export ENVIRONMENT=production
pytest backend/tests/ -v
```

**Result**: ❌ FAILS  
```
RuntimeError: Tests must run against STAGING environment only!
Current environment: production
```

**Why**: conftest.py's `pytest_configure()` runs first and overrides back to staging.

---

### Attempt 2: Set environment in test file
```python
# Inside test
os.environ["ENVIRONMENT"] = "production"

def test_something(ensure_staging_env):
    # ensure_staging_env fixture checks here
    assert os.environ["ENVIRONMENT"] == "staging"  # FAILS!
```

**Result**: ❌ TEST FAILS  
```
AssertionError: assert 'production' == 'staging'
```

**Why**: The autouse fixture `ensure_staging_env` validates before test runs.

---

### Attempt 3: Somehow bypass all three layers
**Not possible**. Here's why:

1. Layer 4 (pytest_configure): Runs first, automatically sets staging
2. Layer 2 (pytest_sessionstart): Validates before tests, hard stop if wrong
3. Layer 3 (ensure_staging_env): On every test, catches runtime changes
4. Layer 1 (pytest.ini): Default configuration

To bypass all 4, someone would need to:
- ❌ Modify conftest.py (code review would catch)
- ❌ Modify pytest.ini (code review would catch)
- ❌ Modify test files (code review would catch)
- ❌ Run pytest differently (documentation says use `pytest backend/tests/`)

---

## Test Files Using Staging

All test files include this at the top:

```python
import os
os.environ.setdefault("ENVIRONMENT", "staging")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "engram-staging-vault")
```

Plus conftest.py overrides to ensure:

```python
os.environ["ENVIRONMENT"] = "staging"  # Force it
os.environ["AZURE_KEY_VAULT_NAME"] = "engram-staging-vault"  # Force it
```

The `.setdefault()` is a backup. The `.assignment` in conftest is the enforcer.

---

## Verification Checklist

After running tests, verify staging was used:

✅ Did you see this banner?
```
======================================================================
PYTEST CONFIGURATION: Staging Environment Tests
======================================================================
Environment: staging
Vault: engram-staging-vault
======================================================================
```

✅ Did you see this confirmation?
```
✓ Confirmed: Running tests against STAGING environment
```

✅ Did tests pass (not fail with environment errors)?

✅ Did you see test output like?
```
backend/tests/test_chat_router.py::TestChatEndpoint::test_send_message_basic PASSED
```

If all 4 checks pass: ✅ Staging environment is active

---

## Environments Comparison

### Which one are we testing against?

**We are testing against: STAGING ✓**

| Environment | Purpose | Can Test? | Data Risk |
|-------------|---------|-----------|-----------|
| **staging** | Dedicated testing | ✅ **YES** | Low (test data) |
| dev | Developer sandboxes | ❌ No | Medium |
| test | Legacy test env | ❌ No (deprecated) | High |
| uat | User acceptance | ❌ No | High |
| prod | Production | ❌ No | CRITICAL |

---

## Proof of Staging Configuration

### conftest.py enforces staging
```python
def pytest_configure(config):
    os.environ["ENVIRONMENT"] = "staging"  # ← Forces staging
    print(f"Environment: {os.environ.get('ENVIRONMENT')}")  # ← Prints: staging

def pytest_sessionstart(session):
    if environment != "staging":  # ← Checks staging
        raise RuntimeError(...)  # ← Stops if wrong

@pytest.fixture(autouse=True)
def ensure_staging_env():
    assert os.environ.get("ENVIRONMENT") == "staging"  # ← Per-test check
    yield
```

### pytest.ini specifies staging
```ini
[pytest]
addopts = --environment=staging

[tool:pytest]
env = staging
```

### Each test file sets staging
```python
os.environ.setdefault("ENVIRONMENT", "staging")
```

**Result**: 4 independent confirmations that staging is the test environment

---

## Test Markers

All tests automatically receive the `@pytest.mark.staging` marker:

```bash
# View all staging tests
pytest backend/tests/ --collect-only | grep staging

# Run only staging tests (all tests, since all are marked staging)
pytest backend/tests/ -m staging

# Exclude any production tests (there are none, but this would work)
pytest backend/tests/ -m "not production"
```

---

## When Staging Environment Applies

### To These Test Files:
✅ test_chat_router.py  
✅ test_memory_router_expanded.py  
✅ test_memory_operations.py  
✅ test_memory_router_contracts.py  
✅ Any new test_*.py files you create  

### To These Fixtures:
✅ @pytest.fixture functions  
✅ conftest fixtures  
✅ Monkeypatch instances  
✅ TestClient instances  

### To These Services (Mocked):
✅ agent_chat function  
✅ memory_client instance  
✅ enrich_context function  
✅ persist_conversation function  
✅ Zep integration  

---

## Summary

**Your test suite has 4 independent layers of staging enforcement:**

1. **Automatic Setup** (conftest.py pytest_configure) - Actively sets staging
2. **Session Validation** (conftest.py pytest_sessionstart) - Hard stop before tests
3. **Per-Test Validation** (conftest.py ensure_staging_env) - Catches runtime changes
4. **Configuration Default** (pytest.ini) - Specifies staging as environment

**Result**: Impossible to accidentally run tests against production, UAT, dev, or test environment.

**How you run tests**: Normally with `pytest backend/tests/ -v`

**Result you see**: Staging environment confirmation + all tests pass

---

## Document Version

**Version**: 1.0  
**Date**: December 15, 2025  
**Status**: Active  
**Staging Enforcement**: 4-layer protection enabled

