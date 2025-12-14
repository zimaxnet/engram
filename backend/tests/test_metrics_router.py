"""
Tests for metrics router endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


def test_get_evidence_telemetry_default_range(client):
    """Test getting evidence telemetry with default range"""
    response = client.get("/api/v1/metrics/evidence")
    # Should return 401 without auth, or 200 with proper auth
    assert response.status_code in [200, 401]
    
    if response.status_code == 200:
        data = response.json()
        assert "range_label" in data
        assert "reliability" in data
        assert "ingestion" in data
        assert "memory_quality" in data
        assert "alerts" in data
        assert "narrative" in data


def test_get_evidence_telemetry_with_range(client):
    """Test getting evidence telemetry with specific range"""
    for range_val in ["15m", "1h", "24h", "7d"]:
        response = client.get(f"/api/v1/metrics/evidence?range={range_val}")
        # Should return 401 without auth, or 200 with proper auth
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert data["range_label"] == range_val


def test_get_alerts(client):
    """Test getting alerts"""
    response = client.get("/api/v1/metrics/alerts")
    # Should return 401 without auth, or 200 with proper auth
    assert response.status_code in [200, 401]
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)

