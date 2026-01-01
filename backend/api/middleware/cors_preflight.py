"""
CORS Preflight Middleware

Handles OPTIONS requests before authentication middleware.
This ensures CORS preflight requests are handled correctly and bypass authentication.

CRITICAL: This middleware must be placed AFTER CORSMiddleware in the middleware stack
so that CORSMiddleware can add CORS headers, but BEFORE authentication middleware
so that OPTIONS requests don't require authentication.
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core import get_settings

logger = logging.getLogger(__name__)


class CORSPreflightMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle OPTIONS requests (CORS preflight) before authentication.
    
    This ensures that OPTIONS requests return proper CORS headers without
    requiring authentication, allowing browsers to complete preflight checks.
    
    FastAPI's CORSMiddleware should handle OPTIONS automatically, but authentication
    dependencies might be evaluated before CORSMiddleware can intercept. This middleware
    ensures OPTIONS requests return immediately with proper CORS headers.
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS requests (CORS preflight) - return immediately with CORS headers
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            
            logger.info(
                f"CORS preflight request: {request.url.path} from origin: {origin or 'unknown'}"
            )
            
            # Validate origin against allowed origins
            allowed_origins = self.settings.cors_origins
            is_allowed = False
            
            if origin:
                # Check if origin is in allowed list
                for allowed in allowed_origins:
                    if allowed == "*" or origin == allowed:
                        is_allowed = True
                        break
            
            # Create response
            response = Response(status_code=200)
            
            # Get requested method and headers from preflight request
            requested_method = request.headers.get(
                "access-control-request-method", 
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            requested_headers = request.headers.get(
                "access-control-request-headers", 
                "authorization, content-type"
            )
            
            # Always add these headers for OPTIONS requests
            response.headers["Access-Control-Allow-Methods"] = requested_method
            response.headers["Access-Control-Allow-Headers"] = requested_headers
            response.headers["Access-Control-Max-Age"] = "3600"
            
            # Add origin header only if origin is allowed
            if is_allowed and origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            elif "*" in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = "*"
            else:
                # Origin not allowed - still return 200 but without Access-Control-Allow-Origin
                # Browser will block the actual request
                logger.warning(f"CORS preflight: origin {origin} not in allowed list: {allowed_origins}")
            
            logger.info(
                f"CORS preflight response: 200 OK for {request.url.path}, "
                f"origin: {origin}, allowed: {is_allowed}"
            )
            return response
        
        # For all other requests, continue to next middleware
        response = await call_next(request)
        return response

