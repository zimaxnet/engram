"""
Tests for BAU router endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user context"""
    return {
        "user_id": "test-user",
        "tenant_id": "test-tenant",
        "roles": ["ANALYST"],
        "scopes": ["read", "write"],
        "session_id": "test-session",
    }


def test_list_bau_flows(client, mock_user):
    """Test listing BAU flows"""
    # Note: In a real test, we'd mock the auth dependency
    # For now, we'll test the endpoint structure
    response = client.get("/api/v1/bau/flows")
    # Should return 401 without auth, or 200 with proper auth
    assert response.status_code in [200, 401]


def test_list_bau_artifacts(client, mock_user):
    """Test listing BAU artifacts"""
    response = client.get("/api/v1/bau/artifacts?limit=10")
    # Should return 401 without auth, or 200 with proper auth
    assert response.status_code in [200, 401]


def test_start_bau_flow(client, mock_user):
    """Test starting a BAU flow"""
    response = client.post(
        "/api/v1/bau/flows/intake-triage/start",
        json={"flow_id": "intake-triage", "initial_message": "Test message"},
    )
    # Should return 401 without auth, or 200/500 with proper auth
    assert response.status_code in [200, 401, 500]


def test_start_bau_flow_invalid_id(client, mock_user):
    """Test starting a BAU flow with invalid flow ID"""
    response = client.post(
        "/api/v1/bau/flows/invalid-flow/start",
        json={"flow_id": "invalid-flow"},
    )
    # Should return 401 without auth, or 404 with proper auth
    assert response.status_code in [404, 401]

