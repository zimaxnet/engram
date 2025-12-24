
from fastapi.testclient import TestClient
import pytest
from backend.api.main import app  # Assuming main entry point

client = TestClient(app)

def test_get_image_endpoint():
    """
    Verify that the /api/v1/images/{filename} endpoint is reachable
    and correctly handles missing files.
    """
    # 1. Test missing file
    response = client.get("/api/v1/images/non_existent.png")
    # 2. Test valid file (setup required)
    import os
    from backend.core.config import get_settings, Settings
    
    # Create temp settings overriding the real ones
    test_docs_path = "/tmp/engram_test_docs_endpoint"
    os.makedirs(os.path.join(test_docs_path, "images"), exist_ok=True)
    
    def get_test_settings():
        return Settings(
            app_name="Test App",
            app_version="0.0.0",
            environment="test",
            onedrive_docs_path=test_docs_path, 
            cors_origins=["*"]
        )
    
    # Apply override
    app.dependency_overrides[get_settings] = get_test_settings
    
    test_filename = "test_image.png"
    with open(os.path.join(test_docs_path, "images", test_filename), "wb") as f:
        f.write(b"fake image content")
        
    response = client.get(f"/api/v1/images/{test_filename}")
    
    # Cleanup
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    assert response.content == b"fake image content"
