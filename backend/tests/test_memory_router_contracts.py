"""Contract tests for Memory API.

NOTE: Mock-based tests deprecated. Use live Zep integration tests.
"""

import pytest

# Skip all tests - mock-based tests deprecated
pytestmark = pytest.mark.skip(reason="Mock-based tests deprecated - use integration tests")

import os

# Set staging environment for testing
os.environ.setdefault("ENVIRONMENT", "staging")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "engram-staging-vault")
os.environ.setdefault("AZURE_KEYVAULT_URL", "https://engram-staging-vault.vault.azure.net/")
os.environ.setdefault("AZURE_AI_ENDPOINT", "")
os.environ.setdefault("AZURE_AI_KEY", "")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    from backend.api.main import app
    from backend.core import Role, SecurityContext
    from backend.api.middleware.auth import get_current_user

    async def override_user():
        return SecurityContext(
            user_id="user-derek",
            tenant_id="tenant-zimax",
            roles=[Role.ANALYST],
            scopes=["*"],
            session_id="session-thread",
        )

    app.dependency_overrides[get_current_user] = override_user

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_memory_search_returns_nodes(client, monkeypatch):
    from datetime import datetime
    from backend.core import GraphNode

    # Patch the module-level memory_client used by the router (imported inside endpoint).
    import backend.memory.client as memory_client_module

    class DummyMemoryClient:
        async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
            return [
                GraphNode(
                    id="fact-1",
                    content="gh-pages branch is static",
                    node_type="fact",
                    confidence=1.0,
                    created_at=datetime.utcnow(),
                    metadata={"filename": "cogai-thread.txt", "source": "document_upload"},
                )
            ]

    monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

    resp = client.post("/api/v1/memory/search", json={"query": "gh-pages", "limit": 5})
    assert resp.status_code == 200

    data = resp.json()
    assert data["total_count"] == 1
    assert data["results"][0]["content"].startswith("gh-pages")
    assert data["results"][0]["metadata"]["filename"] == "cogai-thread.txt"
    assert data["results"][0]["metadata"]["source"] == "document_upload"
