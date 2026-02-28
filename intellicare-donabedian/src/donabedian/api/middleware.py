"""
Custom middleware for the Donabedian API.

Provides logging, error handling, and request tracking.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and their processing time.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            Response: HTTP response
        """
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add custom header with processing time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.3f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                }
            )
            
            return response
            
        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {str(exc)} - Time: {process_time:.3f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "process_time": process_time,
                },
                exc_info=True
            )
            
            # Re-raise exception to be handled by FastAPI
            raise

