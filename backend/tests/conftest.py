import pytest
from unittest.mock import MagicMock
import sys

# Aggressively mock modules before they are imported by tests
mock_settings = MagicMock()
mock_settings.app_name = "Engram Test"
mock_settings.app_version = "0.0.0"
mock_settings.environment = "test"
mock_settings.debug = True
mock_settings.cors_origins = ["*"]
# Important: ensure onedrive_docs_path is a valid string for Path()
mock_settings.onedrive_docs_path = "/tmp" 

# Mock the entire config module
mock_config = MagicMock()
mock_config.get_settings.return_value = mock_settings
sys.modules["backend.core.config"] = mock_config

# Also mock backend.core in case it re-exports
sys.modules["backend.core"] = MagicMock()
sys.modules["backend.core"].get_settings.return_value = mock_settings

# Mock Key Vault and Identity to prevent any Azure interaction
sys.modules["azure.keyvault.secrets"] = MagicMock()
sys.modules["azure.identity"] = MagicMock()
sys.modules["azure.storage.blob"] = MagicMock()

# Mock other potential troublemakers
sys.modules["backend.llm.claude_client"] = MagicMock()
sys.modules["backend.llm.gemini_client"] = MagicMock()

@pytest.fixture
def mock_app():
    # Only import app inside the fixture to ensure mocks are in place
    from backend.api.main import app
    return app

@pytest.fixture
def client(mock_app):
    from fastapi.testclient import TestClient
    return TestClient(mock_app)
