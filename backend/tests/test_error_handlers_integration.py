"""Integration tests for error handlers from util/errors."""

from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app

client = TestClient(app)


def test_http_exception_404_handler():
    """Test that 404 HTTPException returns proper ErrorResponse format."""
    response = client.get("/api/v1/nonexistent-endpoint")
    
    assert response.status_code == 404
    assert "X-Request-Id" in response.headers
    
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "Not Found"  # FastAPI's default 404 message
    assert "requestId" in body["error"]
    assert body["error"]["requestId"] == response.headers["X-Request-Id"]


def test_validation_error_handler():
    """Test that validation errors return proper ErrorResponse format."""
    # Try to call an endpoint with invalid data
    # Since we don't have POST endpoints yet, we'll test with query params
    # This test will be more meaningful when we have actual POST endpoints
    
    # For now, we can test that the handler is registered by checking app state
    from fastapi.exceptions import RequestValidationError
    from app.util.errors import validation_exception_handler
    
    # Check that the handler is registered
    assert RequestValidationError in app.exception_handlers
    assert app.exception_handlers[RequestValidationError] == validation_exception_handler


def test_api_exception_handler():
    """Test that BaseAPIException handler is registered."""
    from app.util.errors import BaseAPIException, api_exception_handler
    
    # Check that the handler is registered
    assert BaseAPIException in app.exception_handlers
    assert app.exception_handlers[BaseAPIException] == api_exception_handler


def test_http_exception_handler():
    """Test that HTTPException handler is registered."""
    from fastapi import HTTPException
    from app.util.errors import http_exception_handler
    
    # Check that the handler is registered
    assert HTTPException in app.exception_handlers
    assert app.exception_handlers[HTTPException] == http_exception_handler


def test_no_duplicate_exception_handlers():
    """Test that main.py doesn't have duplicate custom exception handlers."""
    # Read main.py and check for @app.exception_handler decorators
    import inspect
    import app.main as main_module
    
    source = inspect.getsource(main_module)
    
    # Check that we don't have custom exception handler decorators anymore
    # (they should be replaced by the registered handlers from util/errors)
    assert "@app.exception_handler(404)" not in source
    assert "@app.exception_handler(HTTPException)" not in source
    assert "@app.exception_handler(Exception)" not in source


def test_request_id_in_all_error_responses():
    """Test that X-Request-Id is included in all error responses."""
    # Test with provided request ID
    request_id = "test-request-123"
    response = client.get(
        "/api/v1/nonexistent",
        headers={"X-Request-Id": request_id}
    )
    
    assert response.status_code == 404
    assert response.headers["X-Request-Id"] == request_id
    assert response.json()["error"]["requestId"] == request_id
    
    # Test without provided request ID (should generate one)
    response = client.get("/api/v1/another-nonexistent")
    
    assert response.status_code == 404
    assert "X-Request-Id" in response.headers
    generated_id = response.headers["X-Request-Id"]
    assert response.json()["error"]["requestId"] == generated_id