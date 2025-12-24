import pytest
from unittest.mock import MagicMock
import sys
import os

# Create a temporary directory for docs
from pathlib import Path

# Mock environment variables BEFORE any imports
os.environ["APP_NAME"] = "Engram Test"
os.environ["APP_VERSION"] = "0.0.0"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["ONEDRIVE_DOCS_PATH"] = "/tmp/engram_test_docs"

# Create the temp dir
Path("/tmp/engram_test_docs/images").mkdir(parents=True, exist_ok=True)

# Mock Key Vault/Identity/Blob to prevent Azure connectivity
sys.modules["azure.keyvault.secrets"] = MagicMock()
sys.modules["azure.identity"] = MagicMock()
sys.modules["azure.storage.blob"] = MagicMock()

@pytest.fixture
def mock_app():
    from backend.api.main import app
    return app

@pytest.fixture
def client(mock_app):
    from fastapi.testclient import TestClient
    return TestClient(mock_app)
