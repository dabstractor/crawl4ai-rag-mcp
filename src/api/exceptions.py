"""
Custom exceptions for Crawl4AI MCP HTTP API.

This module defines custom exception classes for different error scenarios
in the HTTP API layer.
"""

from typing import Optional, Dict, Any


class BaseAPIError(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class MCPToolError(BaseAPIError):
    """Exception raised when MCP tool execution fails."""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="MCP_TOOL_ERROR",
            status_code=500,
            details={"tool_name": tool_name, **(details or {})}
        )


class ValidationError(BaseAPIError):
    """Exception raised for validation errors."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, "value": value, **(details or {})}
        )


class NotFoundError(BaseAPIError):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})}
        )


class UnauthorizedError(BaseAPIError):
    """Exception raised for unauthorized access."""
    
    def __init__(
        self, 
        message: str = "Unauthorized access",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
            details=details or {}
        )


class ForbiddenError(BaseAPIError):
    """Exception raised for forbidden access."""
    
    def __init__(
        self, 
        message: str = "Access forbidden",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details or {}
        )


class RateLimitError(BaseAPIError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after, **(details or {})}
        )


class TimeoutError(BaseAPIError):
    """Exception raised when an operation times out."""
    
    def __init__(
        self, 
        message: str = "Request timeout",
        timeout_seconds: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="TIMEOUT",
            status_code=408,
            details={"timeout_seconds": timeout_seconds, **(details or {})}
        )


# Exception handlers utility functions

def handle_exception(exc: Exception) -> dict:
    """
    Convert an exception to a standardized error response dictionary.
    
    Args:
        exc: The exception to handle
        
    Returns:
        Dictionary with error information
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Handle custom API errors
    if isinstance(exc, BaseAPIError):
        logger.error(f"API Error [{exc.code}]: {exc.message}", extra=exc.details)
        return {
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "data": None
        }
    
    # Handle Pydantic validation errors
    elif hasattr(exc, "errors") and callable(getattr(exc, "errors")):
        # Pydantic ValidationError
        errors = exc.errors()
        logger.error(f"Validation Error: {exc}", extra={"errors": errors})
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"validation_errors": errors}
            },
            "data": None
        }
    
    # Handle HTTP exceptions
    elif hasattr(exc, "status_code") and hasattr(exc, "detail"):
        # FastAPI HTTPException
        logger.error(f"HTTP Error {exc.status_code}: {exc.detail}")
        return {
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {"status_code": exc.status_code}
            },
            "data": None
        }
    
    # Handle generic exceptions
    else:
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error_type": type(exc).__name__}
            },
            "data": None
        }


def get_status_code(exc: Exception) -> int:
    """
    Get appropriate HTTP status code for an exception.
    
    Args:
        exc: The exception
        
    Returns:
        HTTP status code
    """
    if isinstance(exc, BaseAPIError):
        return exc.status_code
    elif hasattr(exc, "status_code"):
        return getattr(exc, "status_code", 500)
    else:
        return 500