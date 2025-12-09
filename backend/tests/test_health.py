"""
Basic health check tests
"""

import os

# Set test environment variables BEFORE any backend imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "test-vault")
os.environ.setdefault("AZURE_KEYVAULT_URL", "https://test-vault.vault.azure.net/")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
os.environ.setdefault("AZURE_OPENAI_KEY", "test-key")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "test-deployment")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
os.environ.setdefault("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
os.environ.setdefault("ENTRA_TENANT_ID", "test-tenant")
os.environ.setdefault("ENTRA_CLIENT_ID", "test-client")
os.environ.setdefault("ENTRA_CLIENT_SECRET", "test-secret")

import pytest
from fastapi.testclient import TestClient

# Import after environment is set
from backend.api.main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_readiness_endpoint(client):
    """Test the readiness check endpoint"""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)
