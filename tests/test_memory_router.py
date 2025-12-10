import pytest
from httpx import AsyncClient, ASGITransport
from backend.api.main import app

@pytest.mark.asyncio
async def test_search_memory_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/memory/search", json={"query": "test query", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_count" in data

@pytest.mark.asyncio
async def test_list_episodes_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/memory/episodes?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "episodes" in data
    assert "total_count" in data

@pytest.mark.asyncio
async def test_add_fact_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/memory/facts", json={"content": "Test fact", "confidence": 1.0})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
