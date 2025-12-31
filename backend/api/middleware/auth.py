"""
Microsoft Entra ID Authentication Middleware

Provides:
- JWT token validation from Entra ID
- User identity extraction
- Role-based access control (RBAC)
- Multi-tenant support
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.core import Role, SecurityContext, get_settings

logger = logging.getLogger(__name__)

# Security scheme - with auto_error=False, returns None if no credentials
# This allows us to check AUTH_REQUIRED first before raising 401
security = HTTPBearer(auto_error=False)
security_optional = HTTPBearer(auto_error=False)  # Alias for clarity


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
    Supports both Workforce (login.microsoftonline.com) and External ID (ciamlogin.com).
    """

    def __init__(self):
        self.settings = get_settings()
        self._jwks_cache: Optional[dict] = None
        self._jwks_cache_time: Optional[datetime] = None
        self._jwks_cache_ttl = 3600  # 1 hour
        
        # Check if using External ID (CIAM)
        # External ID tenants use *.ciamlogin.com or *.b2clogin.com
        self._is_external_id = os.environ.get("AZURE_AD_EXTERNAL_ID", "").lower() == "true"
        self._external_id_domain = os.environ.get("AZURE_AD_EXTERNAL_DOMAIN", "")  # e.g., engramai
        
        # Log configuration on initialization
        logger.info(
            f"EntraIDAuth initialized - External ID: {self._is_external_id}, "
            f"Domain: {self._external_id_domain}, Tenant ID: {self.tenant_id}, "
            f"Client ID: {self.client_id}"
        )

    @property
    def tenant_id(self) -> str:
        return self.settings.azure_tenant_id or "common"
    
    @property
    def tenant_domain(self) -> str:
        """Get tenant domain for External ID (e.g., 'engramai' from 'engramai.onmicrosoft.com')"""
        return self._external_id_domain or self.tenant_id.split(".")[0]

    @property
    def client_id(self) -> str:
        return self.settings.azure_client_id or ""

    @property
    def authority(self) -> str:
        if self._is_external_id:
            # External ID uses CIAM login endpoint
            return f"https://{self.tenant_domain}.ciamlogin.com/{self.tenant_id}"
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def jwks_uri(self) -> str:
        if self._is_external_id:
            # External ID JWKS endpoint
            return f"https://{self.tenant_domain}.ciamlogin.com/{self.tenant_id}/discovery/v2.0/keys"
        return f"{self.authority}/discovery/v2.0/keys"

    @property
    def valid_issuers(self) -> list[str]:
        """Get list of valid issuers (both named and GUID-based)"""
        issuers = []
        # Named domain issuer (standard expectation)
        issuers.append(f"https://{self.tenant_domain}.ciamlogin.com/{self.tenant_id}/v2.0")
        
        # GUID-based issuer (what Azure actually sends)
        # Construct assuming tenant_id IS the GUID (which it currently is in .env)
        issuers.append(f"https://{self.tenant_id}.ciamlogin.com/{self.tenant_id}/v2.0")
        
        return issuers

    @property
    def issuer(self) -> str:
        # Keep for backward compatibility if needed, but validation handles lists
        return self.valid_issuers[0]

    async def get_jwks(self, issuer: Optional[str] = None) -> dict:
        """
        Fetch and cache JWKS (JSON Web Key Set) from Entra ID.
        
        Args:
            issuer: Optional issuer URL. If provided, derives JWKS endpoint from issuer.
                    If not provided, uses configured jwks_uri.
        
        Returns:
            JWKS dictionary with keys
        """
        now = datetime.now(timezone.utc)
        
        # Determine JWKS endpoint
        if issuer:
            # Derive JWKS endpoint from token's issuer (standard JWT validation approach)
            # Issuer format: https://{domain}.ciamlogin.com/{tenant_id}/v2.0
            # JWKS format: https://{domain}.ciamlogin.com/{tenant_id}/discovery/v2.0/keys
            jwks_uri = issuer.replace('/v2.0', '/discovery/v2.0/keys')
            cache_key = f"jwks_{issuer}"
        else:
            jwks_uri = self.jwks_uri
            cache_key = "jwks_default"

        # Return cached if valid (check both default and issuer-specific cache)
        if (
            self._jwks_cache is not None
            and self._jwks_cache_time is not None
            and (now - self._jwks_cache_time).seconds < self._jwks_cache_ttl
            and not issuer  # Only use cache for default endpoint
        ):
            return self._jwks_cache

        try:
            logger.info(f"Fetching JWKS from: {jwks_uri}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(jwks_uri)
                response.raise_for_status()
                jwks = response.json()
                
                # Cache only if using default endpoint
                if not issuer:
                    self._jwks_cache = jwks
                    self._jwks_cache_time = now
                
                logger.info(f"Successfully fetched JWKS from {jwks_uri} ({len(jwks.get('keys', []))} keys)")
                return jwks
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch JWKS from {jwks_uri}: HTTP {e.response.status_code}")
            if self._jwks_cache and not issuer:
                logger.warning("Using stale JWKS cache")
                return self._jwks_cache
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to fetch JWKS from {jwks_uri}",
            )
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {jwks_uri}: {e}")
            if self._jwks_cache and not issuer:
                logger.warning("Using stale JWKS cache")
                return self._jwks_cache
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
            # CRITICAL FIX: Decode token WITHOUT verification first to get the issuer
            # This allows us to fetch JWKS from the token's actual issuer (standard JWT validation)
            # Azure CIAM may issue tokens with GUID-based issuers that differ from our configured endpoint
            try:
                unverified_headers = jwt.get_unverified_headers(token)
                unverified_payload = jwt.decode(
                    token,
                    options={"verify_signature": False, "verify_aud": False, "verify_exp": False}
                )
            except Exception as e:
                logger.error(f"Failed to decode token (unverified): {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Extract token claims
            token_issuer = unverified_payload.get("iss")
            token_audience = unverified_payload.get("aud")
            token_tid = unverified_payload.get("tid")
            
            logger.info(
                f"Token claims - iss: {token_issuer}, aud: {token_audience}, tid: {token_tid}"
            )
            
            # Fetch JWKS from the token's issuer (proper JWT validation approach)
            # This handles cases where Azure issues tokens with GUID-based issuers
            try:
                jwks = await self.get_jwks(issuer=token_issuer)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch JWKS from token issuer {token_issuer}, "
                    f"falling back to configured endpoint: {e}"
                )
                # Fallback to configured endpoint
                jwks = await self.get_jwks()
            
            signing_key = self.get_signing_key(token, jwks)

            if not signing_key:
                logger.error(
                    f"Could not find signing key for token. "
                    f"Token KID: {unverified_headers.get('kid')}, "
                    f"JWKS has {len(jwks.get('keys', []))} keys"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token signature - signing key not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Validate audience
            # When requesting scope api://{CLIENT_ID}/user_impersonation, the token audience
            # will be api://{CLIENT_ID}, not just the CLIENT_ID
            # Accept both formats for flexibility
            valid_audiences = []
            if self.client_id:
                # Client ID itself (for .default scope tokens)
                valid_audiences.append(self.client_id)
                # App ID URI format (for api://{CLIENT_ID}/user_impersonation scope tokens)
                valid_audiences.append(f"api://{self.client_id}")
            
            if token_audience not in valid_audiences:
                logger.warning(
                    f"Token audience mismatch: token_aud={token_audience}, "
                    f"expected one of: {valid_audiences}, client_id={self.client_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token audience: {token_audience}. Expected one of: {valid_audiences}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Validate issuer - accept both named domain and GUID-based issuers
            # Build allowed issuers list
            allowed_issuers = self.valid_issuers.copy()
            if token_tid:
                # Add GUID-based issuer for the token's tenant
                allowed_issuers.append(f"https://{token_tid}.ciamlogin.com/{token_tid}/v2.0")
                allowed_issuers.append(f"https://login.microsoftonline.com/{token_tid}/v2.0")
            
            # Also accept the token's own issuer (if it's a valid Azure CIAM issuer)
            if token_issuer and token_issuer.startswith(("https://", "http://")):
                # Only add if it's a CIAM or Microsoftonline issuer
                if ".ciamlogin.com" in token_issuer or "login.microsoftonline.com" in token_issuer:
                    if token_issuer not in allowed_issuers:
                        allowed_issuers.append(token_issuer)
            
            # Decode and validate token with signature verification
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=token_audience,
                options={"verify_at_hash": False, "verify_iss": False},  # We verify issuer manually
            )
            
            # Manual Issuer Check
            if token_issuer not in allowed_issuers:
                logger.warning(
                    f"Token issuer not in allowed list: token_iss={token_issuer}, "
                    f"allowed: {allowed_issuers}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token issuer: {token_issuer}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info(
                f"Token validated successfully - user: {payload.get('oid', payload.get('sub'))}, "
                f"issuer: {token_issuer}"
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
            "Manager": Role.PM,
            "Viewer": Role.VIEWER,
            "admin": Role.ADMIN,
            "analyst": Role.ANALYST,
            "manager": Role.PM,
            "viewer": Role.VIEWER,
            "PM": Role.PM,
            "pm": Role.PM,
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


def _get_auth_required() -> bool:
    """Helper to check AUTH_REQUIRED setting - called at module load time"""
    try:
        # Check environment variable directly first (most reliable)
        env_value = os.environ.get("AUTH_REQUIRED", "").strip().lower()
        if env_value in ("false", "0", "no", "off"):
            logger.info("🔐 AUTH_REQUIRED=false detected from environment variable - auth bypass enabled")
            return False
        
        # Fallback to settings
        settings = get_settings()
        auth_required_value = settings.auth_required
        
        # Check both bool False and string "false"
        is_required = bool(auth_required_value) and str(auth_required_value).lower() != "false"
        
        if not is_required:
            logger.info(f"🔐 AUTH_REQUIRED=false detected from settings (value={auth_required_value}) - auth bypass enabled")
        
        return is_required
    except Exception as e:
        logger.warning(f"Failed to read AUTH_REQUIRED setting: {e}, defaulting to False (bypass)")
        return False

# Check auth requirement at module load time
_AUTH_REQUIRED = _get_auth_required()
logger.info(f"🔐 Auth module loaded: AUTH_REQUIRED={_AUTH_REQUIRED} (module-level check)")

# Create a no-op dependency for when auth is disabled
# This completely bypasses HTTPBearer evaluation
async def _no_auth_dependency() -> Optional[HTTPAuthorizationCredentials]:
    """No-op dependency when auth is disabled - returns None to bypass HTTPBearer"""
    return None

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security if _AUTH_REQUIRED else _no_auth_dependency
    ),
) -> SecurityContext:
    """
    FastAPI dependency to get the current authenticated user.
    
    CRITICAL: Checks AUTH_REQUIRED FIRST before any security validation.
    When AUTH_REQUIRED=false, returns POC user immediately.

    Usage:
        @router.get("/protected")
        async def protected_route(user: SecurityContext = Depends(get_current_user)):
            return {"user": user.user_id}
    """
    # CRITICAL: Check AUTH_REQUIRED FIRST - before any security scheme logic
    # Check both environment variable and settings for maximum reliability
    env_auth_required = os.environ.get("AUTH_REQUIRED", "").strip().lower()
    settings = get_settings()
    auth_required_value = settings.auth_required
    
    # Determine if auth is required (check both sources)
    is_auth_required = True
    if env_auth_required in ("false", "0", "no", "off"):
        is_auth_required = False
        logger.info("🔐 AUTH_REQUIRED=false from environment variable - bypassing auth")
    elif not auth_required_value or str(auth_required_value).lower() == "false":
        is_auth_required = False
        logger.info(f"🔐 AUTH_REQUIRED=false from settings (value={auth_required_value}) - bypassing auth")
    
    # ALWAYS log for debugging
    logger.info(f"🔐 Auth check: env={env_auth_required}, settings={auth_required_value}, required={is_auth_required}, environment={settings.environment}")
    
    # If auth is disabled, return POC user IMMEDIATELY (bypasses all security)
    if not is_auth_required:
        logger.info("✅✅✅ Auth bypass enabled - returning POC user")
        return SecurityContext(
            user_id="poc-user",
            tenant_id=settings.azure_tenant_id or "poc-tenant",
            roles=[Role.ADMIN],
            scopes=["*"],
            session_id=request.headers.get("X-Session-ID", "poc-session"),
        )
    
    # Auth is required - proceed with validation
    logger.info(f"Auth required: {auth_required_value}, proceeding with authentication")
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        security if _AUTH_REQUIRED else _no_auth_dependency
    ),
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
        "/api/v1/workflows": [Role.ADMIN, Role.PM],
        "/api/v1/memory/clear": [Role.ADMIN],
        "/api/v1/agents": [Role.ADMIN, Role.PM, Role.ANALYST],
        "/api/v1/chat": [Role.ADMIN, Role.PM, Role.ANALYST, Role.VIEWER],
        "/api/v1/voice": [Role.ADMIN, Role.PM, Role.ANALYST],
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # For now, just pass through (actual enforcement is in route dependencies)
        await self.app(scope, receive, send)
