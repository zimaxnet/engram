"""Request logging middleware"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and their response times.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2)
            }
        )
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))
        
        return response

