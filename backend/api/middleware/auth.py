"""
Authentication middleware for Microsoft Entra ID

Validates JWT tokens and extracts user context for the Security layer.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core import Role, SecurityContext, get_settings

logger = logging.getLogger(__name__)

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[str]:
    """Extract bearer token from request"""
    if credentials:
        return credentials.credentials
    return None


async def validate_entra_token(token: str) -> dict:
    """
    Validate a Microsoft Entra ID token and return claims.
    
    In production, this validates:
    - Token signature against Entra ID public keys
    - Token expiration
    - Audience (must be this application)
    - Issuer (must be Entra ID)
    """
    settings = get_settings()
    
    # TODO: Implement proper token validation with msal
    # For now, return mock claims in development
    if settings.environment == "development":
        return {
            "sub": "dev-user-123",
            "tid": "dev-tenant-456",
            "preferred_username": "developer@example.com",
            "name": "Developer User",
            "roles": ["engram:admin"]
        }
    
    # Production token validation
    try:
        # Import here to avoid issues if msal not installed
        import msal
        
        # Validate token
        # This is a simplified version - production should use proper validation
        raise NotImplementedError("Production token validation not yet implemented")
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token)
) -> SecurityContext:
    """
    Get the current user's security context from the token.
    
    This is the main dependency for protected routes.
    """
    settings = get_settings()
    
    # In development without token, return a dev user
    if settings.environment == "development" and not token:
        return SecurityContext(
            user_id="dev-user",
            tenant_id="dev-tenant",
            roles=[Role.ADMIN],
            scopes=["*"],
            email="developer@example.com",
            display_name="Developer"
        )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Validate token and get claims
    claims = await validate_entra_token(token)
    
    # Build security context from claims
    roles = []
    for role_str in claims.get("roles", []):
        try:
            roles.append(Role(role_str))
        except ValueError:
            pass  # Ignore unknown roles
    
    return SecurityContext(
        user_id=claims.get("sub", ""),
        tenant_id=claims.get("tid", ""),
        roles=roles,
        scopes=claims.get("scp", "").split() if claims.get("scp") else [],
        email=claims.get("preferred_username"),
        display_name=claims.get("name")
    )


def require_role(required_role: Role):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: SecurityContext = Depends(require_role(Role.ADMIN))):
            ...
    """
    async def role_checker(
        user: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' required"
            )
        return user
    
    return role_checker


def require_scope(required_scope: str):
    """
    Dependency factory for scope-based access control.
    
    Usage:
        @router.get("/hr-data")
        async def hr_endpoint(user: SecurityContext = Depends(require_scope("hr:read"))):
            ...
    """
    async def scope_checker(
        user: SecurityContext = Depends(get_current_user)
    ) -> SecurityContext:
        if not user.has_scope(required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required"
            )
        return user
    
    return scope_checker

