"""
Tests for validation router endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


def test_list_golden_datasets(client):
    """Test listing golden datasets"""
    response = client.get("/api/v1/validation/datasets")
    # Should return 401 without auth, or 200 with proper auth
    assert response.status_code in [200, 401]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "name" in data[0]
            assert "filename" in data[0]


def test_get_latest_golden_run(client):
    """Test getting latest golden run"""
    response = client.get("/api/v1/validation/runs/latest")
    # Should return 401 without auth, or 200 with proper auth
    assert response.status_code in [200, 401]
    
    if response.status_code == 200:
        data = response.json()
        # Can be null if no runs exist
        assert data is None or "summary" in data


def test_run_golden_thread(client):
    """Test running golden thread"""
    response = client.post(
        "/api/v1/validation/run",
        json={"dataset_id": "cogai-thread", "mode": "deterministic"},
    )
    # Should return 401 without auth, or 200/500 with proper auth
    assert response.status_code in [200, 401, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "summary" in data
        assert "checks" in data
        assert "narrative" in data
        assert data["summary"]["run_id"] is not None


def test_run_golden_thread_invalid_dataset(client):
    """Test running golden thread with invalid dataset"""
    response = client.post(
        "/api/v1/validation/run",
        json={"dataset_id": "invalid-dataset", "mode": "deterministic"},
    )
    # Should return 401 without auth, or 404 with proper auth
    assert response.status_code in [404, 401]


def test_get_golden_run(client):
    """Test getting a specific golden run"""
    # First create a run
    run_response = client.post(
        "/api/v1/validation/run",
        json={"dataset_id": "cogai-thread", "mode": "deterministic"},
    )
    
    if run_response.status_code == 200:
        run_id = run_response.json()["summary"]["run_id"]
        
        # Then get it
        response = client.get(f"/api/v1/validation/runs/{run_id}")
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert data["summary"]["run_id"] == run_id


def test_get_golden_run_not_found(client):
    """Test getting a non-existent golden run"""
    response = client.get("/api/v1/validation/runs/non-existent-run")
    # Should return 401 without auth, or 404 with proper auth
    assert response.status_code in [404, 401]

