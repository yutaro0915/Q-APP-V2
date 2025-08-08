"""Test for error handling utilities."""

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.util.errors import (
    ErrorCode,
    ErrorResponse,
    ErrorDetail,
    BaseAPIException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    RateLimitedException,
    ValidationException,
    InternalException,
    http_exception_handler,
    validation_exception_handler,
    api_exception_handler,
)


def test_error_codes():
    """Test error code constants."""
    assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
    assert ErrorCode.UNAUTHORIZED == "UNAUTHORIZED"
    assert ErrorCode.FORBIDDEN == "FORBIDDEN"
    assert ErrorCode.NOT_FOUND == "NOT_FOUND"
    assert ErrorCode.CONFLICT == "CONFLICT"
    assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"
    assert ErrorCode.INTERNAL == "INTERNAL"


def test_error_response_model():
    """Test ErrorResponse Pydantic model."""
    error_response = ErrorResponse(
        error={
            "code": ErrorCode.VALIDATION_ERROR,
            "message": "Validation failed",
            "details": [
                {"field": "title", "reason": "too_short", "required": "1-60 chars"}
            ],
            "requestId": "req_123",
        }
    )
    
    assert error_response.error["code"] == "VALIDATION_ERROR"
    assert error_response.error["message"] == "Validation failed"
    assert len(error_response.error["details"]) == 1
    assert error_response.error["requestId"] == "req_123"


def test_error_response_without_details():
    """Test ErrorResponse without optional fields."""
    error_response = ErrorResponse(
        error={
            "code": ErrorCode.NOT_FOUND,
            "message": "Resource not found",
        }
    )
    
    assert error_response.error["code"] == "NOT_FOUND"
    assert error_response.error["message"] == "Resource not found"
    assert "details" not in error_response.error
    assert "requestId" not in error_response.error


def test_bad_request_exception():
    """Test BadRequestException."""
    exc = BadRequestException("Invalid input")
    assert exc.status_code == 400
    assert exc.code == ErrorCode.VALIDATION_ERROR
    assert exc.message == "Invalid input"
    assert exc.details is None


def test_unauthorized_exception():
    """Test UnauthorizedException."""
    exc = UnauthorizedException()
    assert exc.status_code == 401
    assert exc.code == ErrorCode.UNAUTHORIZED
    assert exc.message == "Authentication required"
    assert exc.details is None


def test_forbidden_exception():
    """Test ForbiddenException."""
    exc = ForbiddenException("Access denied")
    assert exc.status_code == 403
    assert exc.code == ErrorCode.FORBIDDEN
    assert exc.message == "Access denied"


def test_not_found_exception():
    """Test NotFoundException."""
    exc = NotFoundException("Thread not found")
    assert exc.status_code == 404
    assert exc.code == ErrorCode.NOT_FOUND
    assert exc.message == "Thread not found"


def test_conflict_exception():
    """Test ConflictException."""
    exc = ConflictException("Already exists")
    assert exc.status_code == 409
    assert exc.code == ErrorCode.CONFLICT
    assert exc.message == "Already exists"


def test_rate_limited_exception():
    """Test RateLimitedException."""
    exc = RateLimitedException(retry_after=60)
    assert exc.status_code == 429
    assert exc.code == ErrorCode.RATE_LIMITED
    assert exc.message == "Rate limit exceeded"
    assert exc.retry_after == 60


def test_validation_exception_with_details():
    """Test ValidationException with details."""
    details = [
        {"field": "title", "reason": "too_short", "required": "1-60 chars"},
        {"field": "body", "reason": "too_long", "required": "max 10000 chars"},
    ]
    exc = ValidationException(details=details)
    assert exc.status_code == 400
    assert exc.code == ErrorCode.VALIDATION_ERROR
    assert exc.message == "Validation failed"
    assert exc.details == details


def test_internal_exception():
    """Test InternalException."""
    exc = InternalException()
    assert exc.status_code == 500
    assert exc.code == ErrorCode.INTERNAL
    assert exc.message == "Internal server error"


def test_api_exception_handler():
    """Test API exception handler."""
    from starlette.requests import Request
    from starlette.datastructures import Headers
    
    # Mock request with X-Request-Id
    class MockRequest:
        def __init__(self):
            self.headers = Headers({"x-request-id": "req_abc123"})
    
    request = MockRequest()
    exc = NotFoundException("Thread not found")
    
    response = api_exception_handler(request, exc)
    
    assert response.status_code == 404
    # Response body will be serialized, so we check the response data
    import json
    body = json.loads(response.body)
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "Thread not found"
    assert body["error"]["requestId"] == "req_abc123"
    assert response.headers["X-Request-Id"] == "req_abc123"


def test_api_exception_handler_without_request_id():
    """Test API exception handler without request ID."""
    from starlette.requests import Request
    from starlette.datastructures import Headers
    
    class MockRequest:
        def __init__(self):
            self.headers = Headers({})
    
    request = MockRequest()
    exc = BadRequestException("Invalid input")
    
    response = api_exception_handler(request, exc)
    
    assert response.status_code == 400
    import json
    body = json.loads(response.body)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Invalid input"
    # Should have generated a request ID
    assert "requestId" in body["error"]
    assert body["error"]["requestId"].startswith("req_")