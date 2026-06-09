"""
Error Handlers
Custom exception handlers for FastAPI
"""

import logging
from typing import Union, Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(message, status_code=404, details=details)


class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message: str = "Validation error", details: Optional[dict] = None):
        super().__init__(message, status_code=422, details=details)


class DatabaseError(APIError):
    """Database error"""
    def __init__(self, message: str = "Database error", details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class CacheError(APIError):
    """Cache error"""
    def __init__(self, message: str = "Cache error", details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class MLModelError(APIError):
    """ML model error"""
    def __init__(self, message: str = "ML model error", details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(APIError):
    """Authorization error"""
    def __init__(self, message: str = "Not authorized", details: Optional[dict] = None):
        super().__init__(message, status_code=403, details=details)


class RateLimitError(APIError):
    """Rate limit error"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[dict] = None):
        super().__init__(message, status_code=429, details=details)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors
    
    Args:
        request: FastAPI request
        exc: Validation exception
        
    Returns:
        JSON response with error details
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Request validation failed",
            "details": errors,
            "path": str(request.url.path)
        }
    )


async def api_error_handler(
    request: Request,
    exc: APIError
) -> JSONResponse:
    """
    Handle custom API errors
    
    Args:
        request: FastAPI request
        exc: API exception
        
    Returns:
        JSON response with error details
    """
    logger.error(
        f"API error on {request.url.path}: {exc.message}",
        extra={"details": exc.details}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path)
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle general exceptions
    
    Args:
        request: FastAPI request
        exc: Exception
        
    Returns:
        JSON response with error details
    """
    logger.error(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": {
                "type": exc.__class__.__name__,
                "message": str(exc)
            },
            "path": str(request.url.path)
        }
    )


async def http_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle HTTP exceptions
    
    Args:
        request: FastAPI request
        exc: HTTP exception
        
    Returns:
        JSON response with error details
    """
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "An error occurred")
    
    logger.warning(f"HTTP exception on {request.url.path}: {detail}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": "HTTP Error",
            "message": detail,
            "path": str(request.url.path)
        }
    )


def format_error_response(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format error response
    
    Args:
        error_type: Type of error
        message: Error message
        details: Additional details
        path: Request path
        
    Returns:
        Formatted error response
    """
    response: Dict[str, Any] = {
        "error": error_type,
        "message": message
    }
    
    if details:
        response["details"] = details
    
    if path:
        response["path"] = path
    
    return response

# Made with Bob
