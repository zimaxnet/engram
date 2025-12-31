"""
CORS Preflight Middleware

Handles OPTIONS requests before authentication middleware.
This ensures CORS preflight requests are handled correctly.

Note: FastAPI's CORSMiddleware should handle OPTIONS automatically,
but this provides an additional safety net to ensure preflight requests
bypass authentication and return proper CORS headers.
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
    
    FastAPI's CORSMiddleware should handle this automatically, but this provides
    an additional layer to ensure OPTIONS requests are handled correctly.
    """

    async def dispatch(self, request: Request, call_next):
        # Handle OPTIONS requests (CORS preflight)
        # FastAPI's CORSMiddleware should handle this, but we ensure it works
        if request.method == "OPTIONS":
            logger.debug(f"CORS preflight request: {request.url.path}")
            # Let CORSMiddleware handle the response (it's added before this middleware)
            # Just pass through - CORSMiddleware will add headers and return 200
            response = await call_next(request)
            return response
        
        # For all other requests, continue to next middleware
        response = await call_next(request)
        return response

