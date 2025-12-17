"""API tests for ETL ingestion endpoint.

Validates response shape, auth wiring (via dependency override), and metadata provenance.
"""

import os

# Set test environment variables BEFORE any backend imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "test-vault")
os.environ.setdefault("AZURE_KEYVAULT_URL", "https://test-vault.vault.azure.net/")
os.environ.setdefault("AZURE_AI_ENDPOINT", "")
os.environ.setdefault("AZURE_AI_KEY", "")
os.environ.setdefault("AZURE_AI_DEPLOYMENT", "")
os.environ.setdefault("AZURE_AI_PROJECT_NAME", "")
os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
os.environ.setdefault("ENTRA_TENANT_ID", "test-tenant")
os.environ.setdefault("ENTRA_CLIENT_ID", "test-client")
os.environ.setdefault("ENTRA_CLIENT_SECRET", "test-secret")

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


def test_ingest_document_indexes_chunks_with_provenance(client, monkeypatch):
    # Patch processor to deterministic chunks
    from backend.etl.processor import processor

    chunks = [
        {
            "text": "gh-pages branch is static (wiki)",
            "metadata": {"source": "unstructured_etl", "filename": "cogai-thread.txt", "page_number": 1},
        },
        {
            "text": "POST /api/v1/etl/ingest",
            "metadata": {"source": "unstructured_etl", "filename": "cogai-thread.txt", "page_number": 1},
        },
    ]

    monkeypatch.setattr(processor, "process_file", lambda *args, **kwargs: chunks)

    # Spy on ingestion_service.memory_client.add_fact
    # The router delegates to ingestion_service, which uses memory_client
    from backend.etl.ingestion_service import ingestion_service
    
    calls = []

    async def fake_add_fact(*, user_id: str, fact: str, metadata: dict):
        calls.append({"user_id": user_id, "fact": fact, "metadata": metadata})
        return "mock-fact-id"
    
    # We must patch the memory_client instance ON the ingestion_service
    monkeypatch.setattr(ingestion_service.memory_client, "add_fact", fake_add_fact)

    resp = client.post(
        "/api/v1/etl/ingest",
        files={"file": ("cogai-thread.txt", b"dummy", "text/plain")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["filename"] == "cogai-thread.txt"
    assert data["chunks_processed"] == 2

    # Background tasks should have executed and called add_fact twice
    assert len(calls) == 2
    assert calls[0]["user_id"] == "user-derek"

    # Provenance contract: do not let chunk metadata overwrite ingest source/filename
    md0 = calls[0]["metadata"]
    assert md0["source"] == "document_upload"
    assert md0["filename"] == "cogai-thread.txt"
    assert md0["etl_source"] == "unstructured_etl"
    assert md0["etl_filename"] == "cogai-thread.txt"
    assert md0["page_number"] == 1
