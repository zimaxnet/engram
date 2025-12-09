import pytest
from backend.api.middleware.auth import EntraIDAuth
from backend.core import Role, SecurityContext

class TestEntraIDAuth:
    def test_role_mapping(self):
        auth = EntraIDAuth()
        
        # Test exact match
        roles = auth.map_roles(["Admin", "Analyst"])
        assert Role.ADMIN in roles
        assert Role.ANALYST in roles
        
        # Test case insensitivity
        roles = auth.map_roles(["admin", "pm"])
        assert Role.ADMIN in roles
        assert Role.PM in roles
        
        # Test default
        roles = auth.map_roles(["UnknownRole"])
        assert Role.VIEWER in roles
        assert len(roles) == 1

    def test_scope_extraction(self):
        auth = EntraIDAuth()
        
        # Test split
        class MockPayload:
            scp = "user.read data.write"
            
        scopes = auth.extract_scopes(MockPayload())
        assert "user.read" in scopes
        assert "data.write" in scopes
        
        # Test all
        class MockPayloadAll:
            scp = None
            
        scopes = auth.extract_scopes(MockPayloadAll())
        assert "*" in scopes

    def test_dev_token_creation(self):
        auth = EntraIDAuth()
        
        token = "dev_user123_admin"
        payload = auth._create_dev_token(token)
        
        assert payload.sub == "user123"
        assert "admin" in payload.roles
        assert payload.tid == "dev-tenant"
