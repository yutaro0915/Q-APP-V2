"""Error handling utilities for the API."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorCode:
    """Error code constants."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL"


class ErrorDetail(BaseModel):
    """Error detail model."""
    field: Optional[str] = None
    reason: Optional[str] = None
    required: Optional[str] = None


class ErrorResponse(BaseModel):
    """Unified error response model."""
    error: Dict[str, Any]


class BaseAPIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class BadRequestException(BaseAPIException):
    """400 Bad Request."""
    
    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(400, ErrorCode.VALIDATION_ERROR, message, details)


class UnauthorizedException(BaseAPIException):
    """401 Unauthorized."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(401, ErrorCode.UNAUTHORIZED, message, details)


class ForbiddenException(BaseAPIException):
    """403 Forbidden."""
    
    def __init__(
        self,
        message: str = "Access denied",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(403, ErrorCode.FORBIDDEN, message, details)


class NotFoundException(BaseAPIException):
    """404 Not Found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(404, ErrorCode.NOT_FOUND, message, details)


class ConflictException(BaseAPIException):
    """409 Conflict."""
    
    def __init__(
        self,
        message: str = "Conflict",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(409, ErrorCode.CONFLICT, message, details)


class RateLimitedException(BaseAPIException):
    """429 Rate Limited."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(429, ErrorCode.RATE_LIMITED, message, details)
        self.retry_after = retry_after


class ValidationException(BaseAPIException):
    """400 Validation Error with details."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(400, ErrorCode.VALIDATION_ERROR, message, details)


class InternalException(BaseAPIException):
    """500 Internal Server Error."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(500, ErrorCode.INTERNAL, message, details)


def _get_or_generate_request_id(request: Request) -> str:
    """Get request ID from request state or generate a new one."""
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


def api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handle custom API exceptions."""
    request_id = _get_or_generate_request_id(request)
    
    error_body = {
        "code": exc.code,
        "message": exc.message,
    }
    
    if exc.details:
        error_body["details"] = exc.details
    
    error_body["requestId"] = request_id
    
    response_body = {"error": error_body}
    
    headers = {"X-Request-Id": request_id}
    
    # Add rate limit headers if applicable
    if isinstance(exc, RateLimitedException) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    logger.warning(
        "API exception: status=%s code=%s message=%s request_id=%s",
        exc.status_code,
        exc.code,
        exc.message,
        request_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=headers,
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    request_id = _get_or_generate_request_id(request)
    
    # Map HTTP status codes to error codes
    status_to_code = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMITED,
    }
    
    error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL)
    
    error_body = {
        "code": error_code,
        "message": exc.detail or "An error occurred",
        "requestId": request_id,
    }
    
    response_body = {"error": error_body}
    
    headers = {"X-Request-Id": request_id}
    
    logger.warning(
        "HTTP exception: status=%s message=%s request_id=%s",
        exc.status_code,
        exc.detail,
        request_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=headers,
    )


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    request_id = _get_or_generate_request_id(request)
    
    # Convert Pydantic validation errors to our format
    details = []
    for error in exc.errors():
        detail = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "reason": error["type"],
            "message": error["msg"],
        }
        details.append(detail)
    
    error_body = {
        "code": ErrorCode.VALIDATION_ERROR,
        "message": "Validation failed",
        "details": details,
        "requestId": request_id,
    }
    
    response_body = {"error": error_body}
    
    headers = {"X-Request-Id": request_id}
    
    logger.warning(
        "Validation error: details=%s request_id=%s",
        details,
        request_id,
    )
    
    return JSONResponse(
        status_code=400,
        content=response_body,
        headers=headers,
    )