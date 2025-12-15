import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_list_workflows_mock():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/workflows")
    
    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data
    assert data["total_count"] > 0
    # Check if mock data is returned
    assert data["workflows"][0]["workflow_id"] == "mock-wf-1"

@pytest.mark.asyncio
async def test_get_workflow_mock():
    workflow_id = "mock-wf-1"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/workflows/{workflow_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == workflow_id
    assert data["status"] == "running"
