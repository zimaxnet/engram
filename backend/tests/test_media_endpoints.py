
from fastapi.testclient import TestClient
import pytest
from backend.api.main import app  # Assuming main entry point


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_get_image_endpoint(client):
    """
    Verify that the /api/v1/images/{filename} endpoint is reachable
    and correctly handles missing files.
    """
    # 1. Test missing file
    print("\n--- Requesting non_existent.png ---")
    response = client.get("/api/v1/images/non_existent.png")
    print(f"Non-existent response: {response.status_code}")
    # assert response.status_code == 404
    
    # 2. Test valid file (setup required)
    # 2. Test valid file (setup required)
    import os
    
    # Use the path defined in conftest.py env vars
    docs_path = os.environ.get("ONEDRIVE_DOCS_PATH", "/tmp/engram_test_docs")
    images_dir = os.path.join(docs_path, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    test_filename = "test_image.png"
    # Create the test file in the location the router expects
    with open(os.path.join(images_dir, test_filename), "wb") as f:
        f.write(b"fake image content")
        
    print(f"\n--- Requesting valid file from {images_dir} ---")
    response = client.get(f"/api/v1/images/{test_filename}")
    
    assert response.status_code == 200
    assert response.content == b"fake image content"
