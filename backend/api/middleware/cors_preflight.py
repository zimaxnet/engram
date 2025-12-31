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

logger = logging.getLogger(__name__)


class CORSPreflightMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle OPTIONS requests (CORS preflight) before authentication.
    
    This ensures that OPTIONS requests return proper CORS headers without
    requiring authentication, allowing browsers to complete preflight checks.
    
    FastAPI's CORSMiddleware should handle OPTIONS automatically, but authentication
    dependencies might be evaluated before CORSMiddleware can intercept. This middleware
    ensures OPTIONS requests are handled correctly.
    """

    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.info(f"CORS preflight request: {request.url.path} from origin: {request.headers.get('origin', 'unknown')}")
            
            # Get the origin from the request
            origin = request.headers.get("origin")
            
            # Create response - CORSMiddleware (which runs after this) will add CORS headers
            # But we return early to prevent authentication from being evaluated
            response = Response(status_code=200)
            
            # Add basic CORS headers (CORSMiddleware will add more, but this ensures they're present)
            if origin:
                # Check if origin is in allowed list (we'll let CORSMiddleware do the full check)
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # Get requested method and headers from preflight request
            requested_method = request.headers.get("access-control-request-method", "GET, POST, PUT, DELETE, OPTIONS")
            requested_headers = request.headers.get("access-control-request-headers", "authorization, content-type")
            
            response.headers["Access-Control-Allow-Methods"] = requested_method
            response.headers["Access-Control-Allow-Headers"] = requested_headers
            response.headers["Access-Control-Max-Age"] = "3600"
            
            logger.info(f"CORS preflight response: 200 OK for {request.url.path}")
            return response
        
        # For all other requests, continue to next middleware
        response = await call_next(request)
        return response

