"""
Tests for EnterpriseContext
"""

import os

# Set test environment variables before imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AZURE_KEY_VAULT_NAME", "test-vault")

from backend.core import EnterpriseContext, SecurityContext, Role


def test_create_context():
    """Test creating a basic EnterpriseContext"""
    security = SecurityContext(
        user_id="test-user",
        tenant_id="test-tenant",
        session_id="test-session",
        roles=[Role.ANALYST],
        scopes=["*"],
    )
    context = EnterpriseContext(security=security)

    assert context.security.user_id == "test-user"
    assert context.security.tenant_id == "test-tenant"
    assert context.episodic.conversation_id == "test-session"
    assert context.operational.status == "idle"


def test_context_to_llm_context():
    """Test converting context to LLM format"""
    security = SecurityContext(
        user_id="test-user",
        tenant_id="test-tenant",
        session_id="test-session",
        roles=[Role.ANALYST],
        scopes=["*"],
    )
    context = EnterpriseContext(security=security)
    llm_context = context.to_llm_context()

    assert isinstance(llm_context, str)
    assert "test-user" in llm_context
    assert "Session Context" in llm_context

