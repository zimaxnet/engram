
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from pathlib import Path
from backend.api.main import create_app
from backend.core import SecurityContext

@pytest.fixture
def client():
    # Mock auth to bypass login
    app = create_app()
    app.dependency_overrides = {}
    
    # Mock get_current_user
    async def mock_get_current_user():
        from backend.core.context import Role
        return SecurityContext(
            user_id="test-user",
            tenant_id="test-tenant",
            email="test@example.com",
            roles=[Role.VIEWER]
        )
            
    from backend.api.middleware.rbac import get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    return TestClient(app)

@pytest.fixture
def mock_fs(tmp_path):
    # Setup mock filesystem structure
    docs = tmp_path / "docs"
    stories = docs / "stories"
    images = docs / "images"
    diagrams = docs / "diagrams"
    
    stories.mkdir(parents=True)
    images.mkdir(parents=True)
    diagrams.mkdir(parents=True)
    
    # Create a dummy story
    (stories / "story1.md").write_text("# Story 1\nContent 1")
    (images / "story1.png").write_bytes(b"fakeimage")
    (diagrams / "story1.json").write_text("{}")
    
    return docs

def test_list_stories(client, mock_fs):
    with patch("backend.api.routers.story.get_settings") as mock_settings:
        mock_settings.return_value.onedrive_docs_path = str(mock_fs)
        
        response = client.get("/api/v1/story/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["topic"] == "story1"
        assert data[0]["story_id"] == "story1"
        # Verify created_at is readable
        from datetime import datetime
        # This will raise ValueError if not iso format
        assert datetime.fromisoformat(data[0]["created_at"])

def test_get_story(client, mock_fs):
    with patch("backend.api.routers.story.get_settings") as mock_settings:
        mock_settings.return_value.onedrive_docs_path = str(mock_fs)
        
        response = client.get("/api/v1/story/story1")
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "story1"
        assert data["story_content"] == "# Story 1\nContent 1"

def test_get_story_not_found(client, mock_fs):
    with patch("backend.api.routers.story.get_settings") as mock_settings:
        mock_settings.return_value.onedrive_docs_path = str(mock_fs)
        
        response = client.get("/api/v1/story/nonexistent")
        assert response.status_code == 404
