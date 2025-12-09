"""
Microsoft Entra ID Authentication Middleware

Provides:
- JWT token validation from Entra ID
- User identity extraction
- Role-based access control (RBAC)
- Multi-tenant support
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.core import Role, SecurityContext, get_settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """Decoded JWT token payload from Entra ID"""

    sub: str  # Subject (user ID)
    oid: str  # Object ID (unique user identifier)
    tid: str  # Tenant ID
    preferred_username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    roles: list[str] = []
    scp: Optional[str] = None  # Scopes
    aud: str  # Audience
    iss: str  # Issuer
    exp: int  # Expiration
    iat: int  # Issued at
    nbf: Optional[int] = None  # Not before


class EntraIDAuth:
    """
    Microsoft Entra ID authentication handler.

    Validates JWT tokens and extracts user identity.
    """

    def __init__(self):
        self.settings = get_settings()
        self._jwks_cache: Optional[dict] = None
        self._jwks_cache_time: Optional[datetime] = None
        self._jwks_cache_ttl = 3600  # 1 hour

    @property
    def tenant_id(self) -> str:
        return self.settings.azure_tenant_id or "common"

    @property
    def client_id(self) -> str:
        return self.settings.azure_client_id or ""

    @property
    def authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def jwks_uri(self) -> str:
        return f"{self.authority}/discovery/v2.0/keys"

    @property
    def issuer(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"

    async def get_jwks(self) -> dict:
        """Fetch and cache JWKS (JSON Web Key Set) from Entra ID"""
        now = datetime.now(timezone.utc)

        # Return cached if valid
        if (
            self._jwks_cache is not None
            and self._jwks_cache_time is not None
            and (now - self._jwks_cache_time).seconds < self._jwks_cache_ttl
        ):
            return self._jwks_cache

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_uri)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = now
                logger.info("Refreshed JWKS from Entra ID")
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._jwks_cache:
                return self._jwks_cache  # Return stale cache on error
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to validate tokens",
            )

    def get_signing_key(self, token: str, jwks: dict) -> Optional[dict]:
        """Get the signing key for a token from JWKS"""
        try:
            headers = jwt.get_unverified_headers(token)
            kid = headers.get("kid")

            if not kid:
                return None

            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    return key

            return None
        except Exception:
            return None

    async def validate_token(self, token: str) -> TokenPayload:
        """
        Validate a JWT token from Entra ID.

        Args:
            token: The JWT token string

        Returns:
            TokenPayload with decoded claims

        Raises:
            HTTPException if validation fails
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # In development, allow mock tokens
        if self.settings.environment == "development" and token.startswith("dev_"):
            return self._create_dev_token(token)

        try:
            # Get JWKS
            jwks = await self.get_jwks()
            signing_key = self.get_signing_key(token, jwks)

            if not signing_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token signature",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Decode and validate token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={"verify_at_hash": False},
            )

            return TokenPayload(**payload)

        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _create_dev_token(self, token: str) -> TokenPayload:
        """Create a development token for testing"""
        # Parse dev token format: dev_<user_id>_<role>
        parts = token.split("_")
        user_id = parts[1] if len(parts) > 1 else "dev-user"
        role = parts[2] if len(parts) > 2 else "analyst"

        return TokenPayload(
            sub=user_id,
            oid=f"dev-oid-{user_id}",
            tid="dev-tenant",
            preferred_username=f"{user_id}@dev.local",
            name=f"Dev User ({user_id})",
            email=f"{user_id}@dev.local",
            roles=[role],
            aud="dev-client-id",
            iss="https://dev.local",
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
            iat=int(datetime.now(timezone.utc).timestamp()),
        )

    def map_roles(self, token_roles: list[str]) -> list[Role]:
        """Map Entra ID roles to application roles"""
        role_mapping = {
            "Admin": Role.ADMIN,
            "Analyst": Role.ANALYST,
            "Manager": Role.MANAGER,
            "Viewer": Role.VIEWER,
            "admin": Role.ADMIN,
            "analyst": Role.ANALYST,
            "manager": Role.MANAGER,
            "viewer": Role.VIEWER,
        }

        mapped = []
        for role in token_roles:
            if role in role_mapping:
                mapped.append(role_mapping[role])

        # Default to VIEWER if no roles matched
        if not mapped:
            mapped.append(Role.VIEWER)

        return mapped

    def extract_scopes(self, token: TokenPayload) -> list[str]:
        """Extract scopes from token"""
        if token.scp:
            return token.scp.split(" ")
        return ["*"]  # Default to all scopes


# Global auth instance
_auth: Optional[EntraIDAuth] = None


def get_auth() -> EntraIDAuth:
    """Get or create the auth instance"""
    global _auth
    if _auth is None:
        _auth = EntraIDAuth()
    return _auth


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> SecurityContext:
    """
    FastAPI dependency to get the current authenticated user.

    Usage:
        @router.get("/protected")
        async def protected_route(user: SecurityContext = Depends(get_current_user)):
            return {"user": user.user_id}
    """
    settings = get_settings()
    auth = get_auth()

    # In development without token, return mock user
    if settings.environment == "development":
        if credentials is None:
            # Check for dev token in header
            dev_token = request.headers.get("X-Dev-Token")
            if dev_token:
                token = auth._create_dev_token(dev_token)
            else:
                # Return default dev user
                return SecurityContext(
                    user_id="dev-user",
                    tenant_id="dev-tenant",
                    roles=[Role.ADMIN],
                    scopes=["*"],
                    session_id=request.headers.get("X-Session-ID", "dev-session"),
                )
        else:
            token = await auth.validate_token(credentials.credentials)
    else:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = await auth.validate_token(credentials.credentials)

    # Build security context
    return SecurityContext(
        user_id=token.oid,
        tenant_id=token.tid,
        roles=auth.map_roles(token.roles),
        scopes=auth.extract_scopes(token),
        session_id=request.headers.get("X-Session-ID", f"session-{token.oid}"),
        email=token.email,
        name=token.name,
    )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[SecurityContext]:
    """
    FastAPI dependency for optional authentication.

    Returns None if no valid token is provided.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


def require_roles(*required_roles: Role):
    """
    Decorator/dependency to require specific roles.

    Usage:
        @router.get("/admin")
        async def admin_route(user: SecurityContext = Depends(require_roles(Role.ADMIN))):
            return {"admin": True}
    """

    async def role_checker(
        user: SecurityContext = Depends(get_current_user),
    ) -> SecurityContext:
        for role in required_roles:
            if role in user.roles:
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required roles: {[r.value for r in required_roles]}",
        )

    return role_checker


def require_scopes(*required_scopes: str):
    """
    Decorator/dependency to require specific scopes.

    Usage:
        @router.get("/data")
        async def data_route(user: SecurityContext = Depends(require_scopes("data.read"))):
            return {"data": []}
    """

    async def scope_checker(
        user: SecurityContext = Depends(get_current_user),
    ) -> SecurityContext:
        # Wildcard scope grants all access
        if "*" in user.scopes:
            return user

        for scope in required_scopes:
            if scope not in user.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required scope: {scope}",
                )

        return user

    return scope_checker


class RBACMiddleware:
    """
    RBAC Middleware for route-level authorization.

    Checks if the user has permission to access the requested resource.
    """

    # Route permission mapping
    ROUTE_PERMISSIONS = {
        "/api/v1/admin": [Role.ADMIN],
        "/api/v1/workflows": [Role.ADMIN, Role.MANAGER],
        "/api/v1/memory/clear": [Role.ADMIN],
        "/api/v1/agents": [Role.ADMIN, Role.MANAGER, Role.ANALYST],
        "/api/v1/chat": [Role.ADMIN, Role.MANAGER, Role.ANALYST, Role.VIEWER],
        "/api/v1/voice": [Role.ADMIN, Role.MANAGER, Role.ANALYST],
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # For now, just pass through (actual enforcement is in route dependencies)
        await self.app(scope, receive, send)
