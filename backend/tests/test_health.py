"""
Basic health check tests
"""

import os
import pytest
from fastapi.testclient import TestClient

# Set test environment variables before imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "test-vault")
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
os.environ.setdefault("AZURE_OPENAI_KEY", "test-key")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "test-deployment")

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

