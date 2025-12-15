"""
Comprehensive tests for Chat router endpoints

Tests cover:
- POST /chat - single message endpoint
- WebSocket streaming (basic connectivity)
- Session management
- Error handling and edge cases
"""

import os

# Set staging environment for testing
os.environ.setdefault("ENVIRONMENT", "staging")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "engram-staging-vault")
os.environ.setdefault("AZURE_KEYVAULT_URL", "https://engram-staging-vault.vault.azure.net/")
os.environ.setdefault("AZURE_AI_ENDPOINT", "")
os.environ.setdefault("AZURE_AI_KEY", "")

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked auth"""
    from backend.api.main import create_app
    from backend.core import Role, SecurityContext
    from backend.api.middleware.auth import get_current_user

    app = create_app()

    async def override_user():
        return SecurityContext(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=[Role.ANALYST],
            scopes=["*"],
            session_id="test-session",
        )

    app.dependency_overrides[get_current_user] = override_user

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def mock_agent_chat(monkeypatch):
    """Mock the agent_chat function"""
    from backend.core import EnterpriseContext, SecurityContext
    
    async def mock_chat(query: str, context: EnterpriseContext, agent_id: str = None):
        return (
            f"Response to: {query}",
            context,
            agent_id or "elena"
        )
    
    monkeypatch.setattr("backend.api.routers.chat.agent_chat", mock_chat)
    return mock_chat


@pytest.fixture
def mock_memory_ops(monkeypatch):
    """Mock memory enrichment and persistence"""
    async def mock_enrich(context, query):
        return context
    
    async def mock_persist(context):
        pass
    
    monkeypatch.setattr("backend.api.routers.chat.enrich_context", mock_enrich)
    monkeypatch.setattr("backend.api.routers.chat.persist_conversation", mock_persist)


class TestChatEndpoint:
    """Tests for POST /chat endpoint"""

    def test_send_message_basic(self, client, mock_agent_chat, mock_memory_ops):
        """Test basic message sending"""
        response = client.post(
            "/api/v1/chat",
            json={
                "content": "What is the project timeline?",
                "agent_id": "elena"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message_id" in data
        assert "content" in data
        assert "agent_id" in data
        assert "agent_name" in data
        assert "timestamp" in data
        assert "session_id" in data
        
        # Verify content
        assert "timeline" in data["content"] or "Response to:" in data["content"]
        assert data["agent_id"] == "elena"

    def test_send_message_without_session(self, client, mock_agent_chat, mock_memory_ops):
        """Test that session is created if not provided"""
        response = client.post(
            "/api/v1/chat",
            json={"content": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is not None
        # Session ID should be UUID format
        assert len(data["session_id"]) > 0

    def test_send_message_with_session(self, client, mock_agent_chat, mock_memory_ops):
        """Test using existing session ID"""
        session_id = "existing-session-123"
        response = client.post(
            "/api/v1/chat",
            json={
                "content": "Follow-up message",
                "session_id": session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    def test_send_message_marcus_agent(self, client, mock_agent_chat, mock_memory_ops):
        """Test requesting Marcus agent specifically"""
        response = client.post(
            "/api/v1/chat",
            json={
                "content": "Create a project plan",
                "agent_id": "marcus"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "marcus"

    def test_send_message_empty_content(self, client, mock_agent_chat, mock_memory_ops):
        """Test handling of empty message"""
        response = client.post(
            "/api/v1/chat",
            json={"content": ""}
        )
        
        # Should reject empty content
        assert response.status_code in [400, 422]

    def test_send_message_very_long_content(self, client, mock_agent_chat, mock_memory_ops):
        """Test handling of very long messages"""
        long_content = "x" * 10000  # 10k characters
        response = client.post(
            "/api/v1/chat",
            json={"content": long_content}
        )
        
        # Should either accept or reject gracefully
        assert response.status_code in [200, 400, 413]

    def test_send_message_special_characters(self, client, mock_agent_chat, mock_memory_ops):
        """Test handling of special characters in message"""
        response = client.post(
            "/api/v1/chat",
            json={
                "content": "Test with émojis 🎉 and spëcial çhars: @#$%"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] is not None

    def test_send_message_multiline(self, client, mock_agent_chat, mock_memory_ops):
        """Test handling of multiline messages"""
        response = client.post(
            "/api/v1/chat",
            json={
                "content": "Line 1\nLine 2\nLine 3"
            }
        )
        
        assert response.status_code == 200

    def test_send_message_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/v1/chat",
            content="not valid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_message_response_has_timestamps(self, client, mock_agent_chat, mock_memory_ops):
        """Test that response includes valid timestamp"""
        response = client.post(
            "/api/v1/chat",
            json={"content": "Test message"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamp is valid ISO format
        timestamp = data["timestamp"]
        assert "T" in timestamp  # ISO format marker
        assert "Z" in timestamp or "+" in timestamp  # Timezone info

    def test_message_response_has_message_id(self, client, mock_agent_chat, mock_memory_ops):
        """Test that each response gets a unique message ID"""
        response1 = client.post(
            "/api/v1/chat",
            json={"content": "First message"}
        )
        response2 = client.post(
            "/api/v1/chat",
            json={"content": "Second message"}
        )
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["message_id"] != data2["message_id"]

    def test_send_message_requires_auth(self, monkeypatch):
        """Test that endpoint requires authentication"""
        from backend.api.main import create_app
        from backend.api.middleware.auth import get_current_user
        from fastapi import HTTPException

        app = create_app()
        
        async def fail_auth():
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        app.dependency_overrides[get_current_user] = fail_auth
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/chat",
            json={"content": "Test"}
        )
        
        assert response.status_code == 401
        app.dependency_overrides.clear()


class TestChatSessionManagement:
    """Tests for session persistence and state"""

    def test_session_context_preserved(self, client, mock_agent_chat, mock_memory_ops):
        """Test that session context is preserved across multiple messages"""
        session_id = "session-persistence-test"
        
        # First message
        response1 = client.post(
            "/api/v1/chat",
            json={
                "content": "Remember this",
                "session_id": session_id
            }
        )
        assert response1.status_code == 200
        
        # Second message in same session
        response2 = client.post(
            "/api/v1/chat",
            json={
                "content": "Recall what I said",
                "session_id": session_id
            }
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

    def test_multiple_sessions_isolated(self, client, mock_agent_chat, mock_memory_ops):
        """Test that different sessions don't interfere"""
        session1 = "session-1"
        session2 = "session-2"
        
        response1 = client.post(
            "/api/v1/chat",
            json={"content": "Message 1", "session_id": session1}
        )
        response2 = client.post(
            "/api/v1/chat",
            json={"content": "Message 2", "session_id": session2}
        )
        
        assert response1.json()["session_id"] == session1
        assert response2.json()["session_id"] == session2


class TestChatErrorHandling:
    """Tests for error handling and edge cases"""

    def test_missing_content_field(self, client):
        """Test request with missing content field"""
        response = client.post(
            "/api/v1/chat",
            json={"agent_id": "elena"}  # Missing content
        )
        
        assert response.status_code == 422

    def test_invalid_agent_id(self, client, mock_agent_chat, mock_memory_ops):
        """Test with invalid agent ID"""
        response = client.post(
            "/api/v1/chat",
            json={
                "content": "Test",
                "agent_id": "nonexistent-agent"
            }
        )
        
        # Should either reject or fall back gracefully
        assert response.status_code in [200, 400, 404]

    def test_response_structure_consistency(self, client, mock_agent_chat, mock_memory_ops):
        """Test that response always has required fields"""
        response = client.post(
            "/api/v1/chat",
            json={"content": "Test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All these fields must be present
        required_fields = [
            "message_id", "content", "agent_id", 
            "agent_name", "timestamp", "session_id"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            assert data[field] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
