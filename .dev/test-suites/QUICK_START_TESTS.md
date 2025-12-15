# Quick Start: Running Tests (Staging Environment)

**All tests automatically run against STAGING environment only.**

---

## Run All Tests (5 seconds)

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
pytest backend/tests/ -v
```

**Expected Output**:
```
PYTEST CONFIGURATION: Staging Environment Tests
Environment: staging
✓ Confirmed: Running tests against STAGING environment

test_chat_router.py::TestChatEndpoint::test_send_message_basic PASSED
test_chat_router.py::TestChatEndpoint::test_send_message_with_session PASSED
test_memory_router_expanded.py::TestMemorySearchBasic::test_simple_query PASSED
...
```

---

## Run Specific Test File

```bash
pytest backend/tests/test_chat_router.py -v
```

---

## Run Specific Test

```bash
pytest backend/tests/test_chat_router.py::TestChatEndpoint::test_send_message_basic -v
```

---

## Run with Coverage Report

```bash
pytest backend/tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

---

## Run Tests with Detailed Output

```bash
pytest backend/tests/ -v -s
```

The `-s` flag shows print statements (useful for debugging)

---

## Run Only Chat Tests

```bash
pytest backend/tests/test_chat_router.py -v
```

---

## Run Only Memory Tests

```bash
pytest backend/tests/test_memory_router_expanded.py backend/tests/test_memory_operations.py -v
```

---

## Count Total Tests

```bash
pytest backend/tests/ --collect-only | tail -1
```

---

## Run Tests Matching Pattern

```bash
pytest backend/tests/ -k "special_char" -v
```

Runs all tests with "special_char" in the name

---

## Check If Tests Pass (Silent Mode)

```bash
pytest backend/tests/ -q
```

Shows only pass/fail summary (no verbose output)

---

## Parallel Test Execution (Faster)

```bash
pip install pytest-xdist
pytest backend/tests/ -n auto
```

Runs tests in parallel (auto-detects CPU count)

---

## Fail on First Error

```bash
pytest backend/tests/ -x
```

Stops after first failure (useful for debugging)

---

## Verify Staging Environment

All commands above automatically:
- ✅ Set ENVIRONMENT=staging
- ✅ Set AZURE_KEY_VAULT_NAME=engram-staging-vault
- ✅ Validate staging before tests
- ✅ Check staging on every test

**You don't need to set environment variables manually.**

---

## See What Tests Exist

```bash
pytest backend/tests/ --collect-only
```

Lists every test that will run

---

## Run Specific Test Class

```bash
pytest backend/tests/test_chat_router.py::TestChatEndpoint -v
```

---

## Run Tests with Custom Pytest.ini Path

```bash
pytest --config-file=backend/pytest.ini backend/tests/ -v
```

---

## Create New Test and Run It

1. Create file: `backend/tests/test_workflows.py`
   ```python
   import os
   os.environ.setdefault("ENVIRONMENT", "staging")
   
   def test_example():
       assert True
   ```

2. Run it:
   ```bash
   pytest backend/tests/test_workflows.py -v
   ```

**Note**: conftest.py will automatically enforce staging

---

## Check Test Status Summary

```bash
pytest backend/tests/ --tb=no -q
```

Shows only: passed, failed, skipped counts

---

## Debug a Failing Test

```bash
pytest backend/tests/test_chat_router.py::TestChatEndpoint::test_send_message_basic -v -s --tb=long
```

- `-v`: Verbose
- `-s`: Show print output
- `--tb=long`: Full traceback

---

## See Test Coverage by File

```bash
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

Shows which lines are not covered by tests

---

## Measure Test Execution Time

```bash
pytest backend/tests/ --durations=10
```

Shows the 10 slowest tests

---

## Environment Files

These files configure staging-only testing:

- `/backend/tests/conftest.py` - Enforces staging on every test
- `/backend/pytest.ini` - Pytest configuration with staging marker
- `/backend/tests/test_*.py` - All test files (use staging)

---

## Test Files Currently Available

✅ `backend/tests/test_chat_router.py` - Chat endpoint (17 tests)
✅ `backend/tests/test_memory_router_expanded.py` - Memory search (25+ tests)
✅ `backend/tests/test_memory_operations.py` - Memory operations (20+ tests)
✅ `backend/tests/test_memory_router_contracts.py` - Memory contracts (5 tests)

**Total**: 67+ tests, all on staging environment

---

## Safety Guarantee

All tests **automatically** run against **STAGING ONLY**.

No commands needed to enable this. It's automatic:
```bash
# This runs on staging
pytest backend/tests/

# This also runs on staging (environment is forced)
ENVIRONMENT=dev pytest backend/tests/  # ← Still uses staging!

# This also runs on staging (conftest.py overrides)
ENVIRONMENT=production pytest backend/tests/  # ← Still uses staging!
```

The staging environment is enforced at the pytest configuration level, not the shell level.

---

## Common Issues

**Q: Tests are slow**
A: Check if they're hitting real Zep/LLM APIs. Should be mocked. Run with `-v -s` to see output.

**Q: One test fails, should I skip it?**
A: No, fix it. Tests are isolated. Failure in one doesn't mean problem in others.

**Q: Can I run tests in production?**
A: No. conftest.py prevents it. Will raise error if ENVIRONMENT != staging.

**Q: Do I need to set ENVIRONMENT=staging?**
A: No. conftest.py sets it automatically. Just run `pytest backend/tests/`

**Q: Can I run tests against UAT?**
A: Not without code review. Policy is staging-only. See TESTING_STRATEGY_STAGING.md for approval process.

---

## Version Info

- **Test Framework**: pytest 7.x
- **Async Support**: pytest-asyncio
- **Coverage Tool**: pytest-cov
- **Environment**: Staging Only (enforced)
- **Date**: December 15, 2025

---

## Next Steps

1. Run the tests: `pytest backend/tests/ -v`
2. Check coverage: `pytest backend/tests/ --cov=backend --cov-report=html`
3. Implement Phase 2: Workflow tests
4. Implement Phase 3: Agent tests

