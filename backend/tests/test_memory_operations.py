"""
Tests for memory operations: enrichment and persistence

NOTE: These tests rely on mock classes which are deprecated.
Skipping until replaced with integration tests against real Zep.
"""

import pytest

# Skip all tests in this file - mock-based tests deprecated
pytestmark = pytest.mark.skip(reason="Mock-based tests deprecated - use integration tests")

import os

# Set staging environment for testing
os.environ.setdefault("ENVIRONMENT", "staging")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "engram-staging-vault")
os.environ.setdefault("AZURE_KEYVAULT_URL", "https://engram-staging-vault.vault.azure.net/")
os.environ.setdefault("AZURE_AI_ENDPOINT", "")
os.environ.setdefault("AZURE_AI_KEY", "")

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core import EnterpriseContext, SecurityContext, Role, GraphNode


@pytest.fixture
def security_context():
    """Create a test security context"""
    return SecurityContext(
        user_id="test-user",
        tenant_id="test-tenant",
        roles=[Role.ANALYST],
        scopes=["*"],
        session_id="test-session",
    )


@pytest.fixture
def enterprise_context(security_context):
    """Create a test enterprise context"""
    context = EnterpriseContext(security=security_context)
    context.episodic.conversation_id = "test-conversation"
    return context


class TestContextEnrichment:
    """Tests for context enrichment with memory"""

    @pytest.mark.asyncio
    async def test_enrich_context_adds_facts(self, enterprise_context, monkeypatch):
        """Test that enrichment adds relevant facts to context"""
        from backend.memory import enrich_context

        # Mock memory client
        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Project timeline: Q1 launch",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={"source": "requirements"},
                    ),
                    GraphNode(
                        id="fact-2",
                        content="Team size: 5 engineers",
                        node_type="fact",
                        confidence=0.90,
                        created_at=datetime.utcnow(),
                        metadata={"source": "staffing"},
                    )
                ]

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        enriched = await enrich_context(enterprise_context, "What is the timeline?")

        # Context should be enriched with facts
        assert enriched is not None
        # Facts should be added to context (implementation-dependent)
        # We're testing the happy path here

    @pytest.mark.asyncio
    async def test_enrich_context_handles_no_facts(self, enterprise_context, monkeypatch):
        """Test enrichment when no relevant facts found"""
        from backend.memory import enrich_context

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                return []

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        enriched = await enrich_context(enterprise_context, "Unknown topic")

        # Should still return context, just without enrichment
        assert enriched is not None

    @pytest.mark.asyncio
    async def test_enrich_context_empty_query(self, enterprise_context, monkeypatch):
        """Test enrichment with empty query"""
        from backend.memory import enrich_context

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                return []

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        enriched = await enrich_context(enterprise_context, "")

        assert enriched is not None

    @pytest.mark.asyncio
    async def test_enrich_context_preserves_context_state(self, enterprise_context, monkeypatch):
        """Test that enrichment doesn't lose existing context"""
        from backend.memory import enrich_context

        original_user = enterprise_context.security.user_id
        original_conversation = enterprise_context.episodic.conversation_id

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
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

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        enriched = await enrich_context(enterprise_context, "Test")

        # Original context should be preserved
        assert enriched.security.user_id == original_user
        assert enriched.episodic.conversation_id == original_conversation


class TestConversationPersistence:
    """Tests for persisting conversation to memory"""

    @pytest.mark.asyncio
    async def test_persist_conversation_saves_message(self, enterprise_context, monkeypatch):
        """Test that conversation is persisted to memory"""
        from backend.memory import persist_conversation

        # Mock memory client
        called_with = {}

        class DummyMemoryClient:
            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                called_with["user_id"] = user_id
                called_with["conversation_id"] = conversation_id
                called_with["messages"] = messages
                return {"id": "saved-1"}

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        # Add a message to context
        enterprise_context.episodic.messages.append({
            "role": "user",
            "content": "What is the project timeline?",
            "timestamp": datetime.utcnow().isoformat()
        })
        enterprise_context.episodic.messages.append({
            "role": "assistant",
            "content": "The project timeline is Q1 2024",
            "timestamp": datetime.utcnow().isoformat()
        })

        await persist_conversation(enterprise_context)

        # Verify persistence was called with correct data
        assert called_with.get("user_id") == "test-user"
        assert called_with.get("conversation_id") == "test-conversation"

    @pytest.mark.asyncio
    async def test_persist_conversation_empty_messages(self, enterprise_context, monkeypatch):
        """Test persistence when no messages to save"""
        from backend.memory import persist_conversation

        class DummyMemoryClient:
            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                return None

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        # No messages to persist
        enterprise_context.episodic.messages = []

        # Should handle gracefully
        await persist_conversation(enterprise_context)

    @pytest.mark.asyncio
    async def test_persist_conversation_preserves_metadata(self, enterprise_context, monkeypatch):
        """Test that conversation metadata is preserved"""
        from backend.memory import persist_conversation

        captured_metadata = {}

        class DummyMemoryClient:
            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                captured_metadata.update(kwargs)
                return {"id": "saved-1"}

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        # Add message with metadata
        enterprise_context.episodic.messages.append({
            "role": "user",
            "content": "Test message",
            "metadata": {"source": "ui"}
        })

        await persist_conversation(enterprise_context)

        # Metadata should be preserved if used

    @pytest.mark.asyncio
    async def test_persist_conversation_handles_error(self, enterprise_context, monkeypatch):
        """Test error handling in persistence"""
        from backend.memory import persist_conversation

        class DummyMemoryClient:
            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                raise Exception("Memory service error")

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        enterprise_context.episodic.messages.append({
            "role": "user",
            "content": "Test"
        })

        # Should handle error gracefully (not raise)
        await persist_conversation(enterprise_context)

    @pytest.mark.asyncio
    async def test_persist_conversation_multiple_turns(self, enterprise_context, monkeypatch):
        """Test persistence of multi-turn conversation"""
        from backend.memory import persist_conversation

        conversation_saves = []

        class DummyMemoryClient:
            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                conversation_saves.append({
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "message_count": len(messages)
                })
                return {"id": f"saved-{len(conversation_saves)}"}

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        # Simulate multi-turn conversation
        turns = [
            ("user", "Hello"),
            ("assistant", "Hi there"),
            ("user", "How are you?"),
            ("assistant", "I'm doing well"),
        ]

        for role, content in turns:
            enterprise_context.episodic.messages.append({
                "role": role,
                "content": content,
            })

        await persist_conversation(enterprise_context)

        assert len(conversation_saves) > 0
        assert conversation_saves[0]["message_count"] == 4


class TestMemoryIntegration:
    """Integration tests for memory enrichment + persistence"""

    @pytest.mark.asyncio
    async def test_enrich_then_persist_workflow(self, enterprise_context, monkeypatch):
        """Test complete enrichment -> response -> persist workflow"""
        from backend.memory import enrich_context, persist_conversation

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                return [
                    GraphNode(
                        id="fact-1",
                        content="Relevant fact",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={},
                    )
                ]

            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                return {"id": "saved-1"}

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        # Step 1: Enrich context
        enriched = await enrich_context(enterprise_context, "What is the timeline?")
        assert enriched is not None

        # Step 2: Simulate agent response
        enriched.episodic.messages.append({
            "role": "assistant",
            "content": "The timeline is Q1 2024",
        })

        # Step 3: Persist conversation
        await persist_conversation(enriched)

    @pytest.mark.asyncio
    async def test_concurrent_enrichment_requests(self, enterprise_context, monkeypatch):
        """Test handling of concurrent enrichment requests"""
        from backend.memory import enrich_context
        import asyncio

        class DummyMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                # Simulate some async work
                await asyncio.sleep(0.01)
                return [
                    GraphNode(
                        id="fact-1",
                        content="Fact",
                        node_type="fact",
                        confidence=0.95,
                        created_at=datetime.utcnow(),
                        metadata={},
                    )
                ]

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", DummyMemoryClient())

        # Make concurrent requests
        queries = ["timeline", "budget", "team size"]
        contexts = [enterprise_context] * len(queries)

        results = await asyncio.gather(*[
            enrich_context(ctx, q)
            for ctx, q in zip(contexts, queries)
        ])

        assert len(results) == len(queries)
        assert all(r is not None for r in results)


class TestMemoryErrorHandling:
    """Tests for error handling in memory operations"""

    @pytest.mark.asyncio
    async def test_enrich_handles_timeout(self, enterprise_context, monkeypatch):
        """Test handling of memory client timeout"""
        from backend.memory import enrich_context
        import asyncio

        class SlowMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                # Simulate timeout
                await asyncio.sleep(10)
                return []

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", SlowMemoryClient())

        # Should handle timeout gracefully
        try:
            enriched = await asyncio.wait_for(
                enrich_context(enterprise_context, "test"),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            # This is acceptable - client should handle timeouts
            pass

    @pytest.mark.asyncio
    async def test_persist_handles_connection_error(self, enterprise_context, monkeypatch):
        """Test handling of connection errors during persistence"""
        from backend.memory import persist_conversation

        class FailingMemoryClient:
            async def add_memory(self, user_id: str, conversation_id: str, messages: list, **kwargs):
                raise ConnectionError("Cannot reach memory service")

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", FailingMemoryClient())

        enterprise_context.episodic.messages.append({
            "role": "user",
            "content": "Test"
        })

        # Should not raise - graceful degradation
        await persist_conversation(enterprise_context)

    @pytest.mark.asyncio
    async def test_enrich_handles_invalid_response(self, enterprise_context, monkeypatch):
        """Test handling of invalid response from memory client"""
        from backend.memory import enrich_context

        class BadMemoryClient:
            async def get_facts(self, user_id: str, query: str = None, limit: int = 5):
                return "invalid"  # Should be list

        import backend.memory.client as memory_module
        monkeypatch.setattr(memory_module, "memory_client", BadMemoryClient())

        # Should handle gracefully
        enriched = await enrich_context(enterprise_context, "test")
        assert enriched is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
