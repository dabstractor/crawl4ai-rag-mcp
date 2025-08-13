"""
HTTP middleware for Crawl4AI MCP Server API.

This module provides middleware components for CORS, request logging,
rate limiting, and security headers.
"""

from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp
from typing import Callable, Dict, Any
import time
import logging
import json
import os
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request with forwarded header support.
    
    This utility function checks for common forwarded headers before
    falling back to the direct client IP.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        str: Client IP address or "unknown" if not available
    """
    # Check for forwarded headers first (common in production with proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    return getattr(request.client, "host", "unknown") if request.client else "unknown"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for logging HTTP requests and responses.
    
    Features:
    - Correlation IDs for request tracking
    - Query parameters logging
    - Configurable log levels based on environment
    - Detailed timing information
    - Error handling with proper logging
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Configure log level based on environment
        self.log_level = self._get_log_level()
        
    def _get_log_level(self) -> int:
        """Get log level from environment variable."""
        log_level_str = os.getenv("REQUEST_LOG_LEVEL", "INFO").upper()
        return getattr(logging, log_level_str, logging.INFO)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details with correlation ID."""
        # Generate correlation ID for request tracking
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Extract query parameters
        query_params = dict(request.query_params) if request.query_params else {}
        query_str = f"?{str(request.query_params)}" if query_params else ""
        
        # Log request details
        if logger.isEnabledFor(self.log_level):
            logger.log(
                self.log_level,
                f"Request {request_id}: {request.method} {request.url.path}{query_str}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": query_params,
                    "client_ip": get_client_ip(request),
                    "user_agent": request.headers.get("User-Agent", "unknown")
                }
            )
        
        # Process request with error handling
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log successful response
            if logger.isEnabledFor(self.log_level):
                logger.log(
                    self.log_level,
                    f"Response {request_id}: {response.status_code} completed in {process_time:.3f}s",
                    extra={
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "process_time": process_time,
                        "response_size": response.headers.get("Content-Length", "unknown")
                    }
                )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error with full context
            logger.error(
                f"Error {request_id}: {str(e)} after {process_time:.3f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": query_params,
                    "process_time": process_time,
                    "error_type": type(e).__name__,
                    "client_ip": get_client_ip(request)
                },
                exc_info=True
            )
            
            # Re-raise the exception to be handled by error middleware
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app: ASGIApp, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.clients: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        client_ip = get_client_ip(request)
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip] 
            if timestamp > minute_ago
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_ip}")
            return Response(
                content=json.dumps({
                    "success": False,
                    "error": "Rate limit exceeded. Please try again later.",
                    "data": None
                }),
                status_code=429,
                headers={"Content-Type": "application/json"}
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.calls_per_minute - len(self.clients[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        return response


def setup_cors_middleware(app, allowed_origins: list = None) -> None:
    """
    Setup CORS middleware for the FastAPI app.
    
    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins for CORS
    """
    if allowed_origins is None:
        # Check for environment variable configuration
        cors_origins_env = os.getenv("CORS_ORIGINS")
        
        if cors_origins_env:
            if cors_origins_env.strip() == "*":
                allowed_origins = ["*"]
            else:
                # Split comma-separated origins and strip whitespace
                allowed_origins = [origin.strip() for origin in cors_origins_env.split(",")]
        else:
            # Default allowed origins for development
            allowed_origins = [
                "http://localhost:3741",  # UI default port
                "http://localhost:3000",  # Common React dev port
                "http://127.0.0.1:3741",
                "http://127.0.0.1:3000",
                "http://localhost:8051",  # MCP server port
                "http://127.0.0.1:8051"
            ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],  # Focus on essential methods
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        expose_headers=["X-Process-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    )
    
    logger.info(f"CORS middleware configured with origins: {allowed_origins}")


def setup_middleware_stack(app, enable_rate_limiting: bool = True, 
                          rate_limit_calls_per_minute: int = 60) -> None:
    """
    Setup the complete middleware stack for the API.
    
    Args:
        app: FastAPI application instance
        enable_rate_limiting: Whether to enable rate limiting
        rate_limit_calls_per_minute: Rate limit threshold
    """
    # Error handling (first, to catch all exceptions)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting (if enabled)
    if enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware, calls_per_minute=rate_limit_calls_per_minute)
        logger.info(f"Rate limiting enabled: {rate_limit_calls_per_minute} calls per minute")
    
    # Request logging (last, to capture all request details)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add global exception handlers
    add_exception_handlers(app)
    
    logger.info("Middleware stack configured successfully")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions and convert them to standardized error responses."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the error with full traceback
            logger.error(
                f"Unhandled exception in {request.method} {request.url}: {exc}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "client": getattr(request.client, "host", "unknown") if request.client else "unknown"
                }
            )
            
            # Import error handling utilities
            try:
                from .exceptions import handle_exception, get_status_code
                error_response = handle_exception(exc)
                status_code = get_status_code(exc)
            except Exception:
                # Fallback if exception handling itself fails
                error_response = {
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {"error_type": type(exc).__name__}
                    },
                    "data": None
                }
                status_code = 500
                logger.error("Error handling failed", exc_info=True)
            
            # Return JSON response
            return JSONResponse(
                status_code=status_code,
                content=error_response
            )


def add_exception_handlers(app) -> None:
    """
    Add global exception handlers to the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    from .exceptions import BaseAPIError, handle_exception, get_status_code
    
    @app.exception_handler(BaseAPIError)
    async def api_error_handler(request: Request, exc: BaseAPIError):
        """Handle custom API errors."""
        logger.error(f"API Error [{exc.code}]: {exc.message}", extra=exc.details)
        error_response = handle_exception(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.error(f"HTTP Error {exc.status_code}: {exc.detail}")
        error_response = handle_exception(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        error_response = handle_exception(exc)
        status_code = get_status_code(exc)
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )


def add_cors_middleware(app) -> None:
    """
    Add CORS middleware to the FastAPI app as specified in Task #3.
    
    This function follows the exact specification from the TaskMaster requirements:
    - Allow all origins initially for development ("*") 
    - Support environment variable configuration for production (CORS_ORIGINS)
    - Allow GET, POST, OPTIONS methods
    - Allow Content-Type and Authorization headers
    - Handle preflight OPTIONS requests correctly
    
    Args:
        app: FastAPI application instance
    """
    # Get origins from environment variable, default to "*" for development
    origins = os.getenv("CORS_ORIGINS", "*")
    
    if origins == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [origin.strip() for origin in origins.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    
    logger.info(f"CORS middleware added with origins: {allowed_origins}")