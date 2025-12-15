"""
Expanded tests for Memory router endpoints

Tests cover:
- Memory search with various inputs (empty, special chars, large result sets)
- Edge cases and error handling
- Response format validation
- Performance considerations
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
from datetime import datetime
from backend.core import GraphNode, Role, SecurityContext


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked auth"""
    from backend.api.main import create_app
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


class TestMemorySearchBasic:
    """Basic memory search tests"""

    def test_search_memory_simple_query(self, client, monkeypatch):
        """Test basic memory search"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Project deadline is March 15",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={"source": "meeting", "attendees": ["Alice", "Bob"]},
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "deadline", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert "deadline" in data["results"][0]["content"]
        assert data["results"][0]["confidence"] == 0.95

    def test_search_memory_multiple_results(self, client, monkeypatch):
        """Test search returning multiple results"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id=f"fact-{i}",
                        content=f"Fact {i}: Project detail",
                        node_type="fact",
                        confidence=0.90 - (i * 0.05),
                        created_at=datetime.utcnow(),
                        metadata={"index": i},
                    )
                    for i in range(5)
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "project", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 5
        assert len(data["results"]) == 5
        # Should be ordered by confidence
        for i, result in enumerate(data["results"]):
            assert result["confidence"] == 0.90 - (i * 0.05)

    def test_search_memory_empty_results(self, client, monkeypatch):
        """Test search with no results"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return []

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "nonexistent-topic", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert len(data["results"]) == 0

    def test_search_response_has_query_time(self, client, monkeypatch):
        """Test that response includes query timing"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Test fact",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={},
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert "query_time_ms" in data
        assert data["query_time_ms"] >= 0


class TestMemorySearchEdgeCases:
    """Edge case tests for memory search"""

    def test_search_with_special_characters(self, client, monkeypatch):
        """Test search with special characters in query"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="GitHub PR #123: Fix @deprecated",
                        node_type="fact",
                        confidence=0.85,
                        created_at=datetime.utcnow(),
                        metadata={"repo": "engram"},
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "@deprecated PR #123", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_search_with_unicode_characters(self, client, monkeypatch):
        """Test search with unicode characters"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Meeting with José García about café production",
                        node_type="fact",
                        confidence=0.90,
                        created_at=datetime.utcnow(),
                        metadata={"language": "spanish"},
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "José café", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_search_with_emoji(self, client, monkeypatch):
        """Test search with emoji characters"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="🚀 Product launch scheduled for Q1 🎯",
                        node_type="fact",
                        confidence=0.92,
                        created_at=datetime.utcnow(),
                        metadata={"priority": "high"},
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "launch 🚀", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1

    def test_search_with_very_long_query(self, client, monkeypatch):
        """Test search with very long query string"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return []

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        long_query = "word " * 1000  # Very long query
        response = client.post(
            "/api/v1/memory/search",
            json={"query": long_query, "limit": 10}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 413]

    def test_search_with_empty_query(self, client, monkeypatch):
        """Test search with empty query string"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return []

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "", "limit": 10}
        )

        # Empty query should be handled (reject or return all)
        assert response.status_code in [200, 400]

    def test_search_with_whitespace_only_query(self, client, monkeypatch):
        """Test search with whitespace-only query"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return []

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "   \n\t  ", "limit": 10}
        )

        # Whitespace query should be handled
        assert response.status_code in [200, 400]

    def test_search_with_large_limit(self, client, monkeypatch):
        """Test search with very large limit parameter"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                # Return fewer results than requested
                return [
                    GraphNode(
                        id=f"fact-{i}",
                        content=f"Fact {i}",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={},
                    )
                    for i in range(5)
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10000}  # Very large limit
        )

        assert response.status_code == 200
        data = response.json()
        # Should return only available results
        assert data["total_count"] == 5

    def test_search_with_zero_limit(self, client, monkeypatch):
        """Test search with zero limit"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return []

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 0}
        )

        # Zero limit should be rejected or handled
        assert response.status_code in [200, 400]


class TestMemorySearchResponseFormat:
    """Tests for response format validation"""

    def test_search_response_structure(self, client, monkeypatch):
        """Test that response has correct structure"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Test fact",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={"key": "value"},
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "results" in data
        assert "total_count" in data
        assert "query_time_ms" in data

        # Check result structure
        result = data["results"][0]
        assert "id" in result
        assert "content" in result
        assert "node_type" in result
        assert "confidence" in result
        assert "created_at" in result
        assert "metadata" in result

    def test_search_node_metadata_preserved(self, client, monkeypatch):
        """Test that node metadata is preserved in response"""
        import backend.memory.client as memory_client_module

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Test",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={
                            "source": "document",
                            "filename": "report.pdf",
                            "page": 5,
                            "tags": ["important", "urgent"]
                        },
                    )
                ]

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10}
        )

        assert response.status_code == 200
        data = response.json()
        metadata = data["results"][0]["metadata"]

        assert metadata["source"] == "document"
        assert metadata["filename"] == "report.pdf"
        assert metadata["page"] == 5
        assert "important" in metadata["tags"]


class TestMemorySearchPermissions:
    """Tests for permission and security"""

    def test_search_requires_auth(self, monkeypatch):
        """Test that search requires authentication"""
        from backend.api.main import create_app
        from backend.api.middleware.auth import get_current_user
        from fastapi import HTTPException

        app = create_app()

        async def fail_auth():
            raise HTTPException(status_code=401, detail="Unauthorized")

        app.dependency_overrides[get_current_user] = fail_auth
        client = TestClient(app)

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10}
        )

        assert response.status_code == 401
        app.dependency_overrides.clear()

    def test_search_respects_user_id(self, client, monkeypatch):
        """Test that search is scoped to user"""
        import backend.memory.client as memory_client_module

        captured_user_id = None

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 20):
                nonlocal captured_user_id
                captured_user_id = user_id
                return []

        monkeypatch.setattr(memory_client_module, "memory_client", DummyMemoryClient())

        response = client.post(
            "/api/v1/memory/search",
            json={"query": "test", "limit": 10}
        )

        assert response.status_code == 200
        # Verify user_id was passed to memory client
        assert captured_user_id == "test-user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
