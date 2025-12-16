"""
Global pytest configuration for staging environment testing

This conftest ensures:
- All tests run against staging environment
- Environment variables are properly configured
- No tests accidentally run against production
- Proper cleanup and teardown
"""

import os
import sys
import pytest


def pytest_configure(config):
    """Configure pytest to enforce staging environment"""
    # Force staging environment before any imports
    os.environ["ENVIRONMENT"] = "staging"
    os.environ["AZURE_KEY_VAULT_NAME"] = "engram-staging-vault"
    os.environ["AZURE_KEYVAULT_URL"] = "https://engram-staging-vault.vault.azure.net/"
    os.environ["AZURE_AI_ENDPOINT"] = os.environ.get("AZURE_AI_ENDPOINT", "")
    os.environ["AZURE_AI_KEY"] = os.environ.get("AZURE_AI_KEY", "")
    
    print(f"\n{'='*70}")
    print(f"PYTEST CONFIGURATION: Staging Environment Tests")
    print(f"{'='*70}")
    print(f"Environment: {os.environ.get('ENVIRONMENT')}")
    print(f"Vault: {os.environ.get('AZURE_KEY_VAULT_NAME')}")
    print(f"{'='*70}\n")


def pytest_sessionstart(session):
    """Verify staging environment is set before running tests"""
    environment = os.environ.get("ENVIRONMENT", "").lower()
    
    if environment != "staging":
        raise RuntimeError(
            f"\n{'='*70}\n"
            f"ERROR: Tests must run against STAGING environment only!\n"
            f"Current environment: {environment}\n"
            f"Allowed environments: staging\n"
            f"{'='*70}\n"
        )
    
    print(f"\n✓ Confirmed: Running tests against STAGING environment")


@pytest.fixture(scope="session")
def environment_check():
    """Fixture to ensure staging environment throughout session"""
    assert os.environ.get("ENVIRONMENT") == "staging", \
        "Environment must be staging for all tests"
    yield
    # Cleanup
    print("\n✓ Test session completed in staging environment")


@pytest.fixture(autouse=True)
def ensure_staging_env(environment_check):
    """Auto-use fixture to ensure staging for every test"""
    assert os.environ.get("ENVIRONMENT") == "staging", \
        "Each test must run in staging environment"
    yield


@pytest.fixture
def staging_info():
    """Provide staging environment information to tests"""
    return {
        "environment": "staging",
        "vault_name": "engram-staging-vault",
        "vault_url": "https://engram-staging-vault.vault.azure.net/",
        "is_staging": True,
        "is_production": False,
    }


def pytest_collection_modifyitems(config, items):
    """Add staging marker to all tests"""
    for item in items:
        # Add staging marker to all tests
        item.add_marker(pytest.mark.staging)
@pytest.fixture
def mock_agent_services(monkeypatch):
    """Mock backend services used by MCP tool"""
    # Mock agent_chat
    async def mock_chat(query, context, agent_id=None):
        return f"MCP Response to: {query}", context, agent_id or "elena"
    
    monkeypatch.setattr("backend.api.routers.mcp.agent_chat", mock_chat)

    # Mock enrich_context
    async def mock_enrich(context, text):
        return context
    
    monkeypatch.setattr("backend.api.routers.mcp.enrich_context", mock_enrich)

    # Mock persist_conversation
    async def mock_persist(context):
        return True
    
    monkeypatch.setattr("backend.api.routers.mcp.persist_conversation", mock_persist)
