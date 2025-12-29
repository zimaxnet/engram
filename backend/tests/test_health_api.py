
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path
from backend.api.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_readiness_check_success(client, tmp_path):
    # Mock settings to point to tmp_path
    with patch("backend.api.routers.health.get_settings") as mock_settings:
        mock_settings.return_value.onedrive_docs_path = str(tmp_path)
        
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["storage"] is True

def test_readiness_check_failure(client):
    # Mock settings to point to a read-only or invalid path
    with patch("backend.api.routers.health.get_settings") as mock_settings:
        mock_settings.return_value.onedrive_docs_path = "/invalid/path/that/cannot/exist"
        
        response = client.get("/ready")
        assert response.status_code == 200  # Still returns 200 but status is degraded
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["storage"] is False
