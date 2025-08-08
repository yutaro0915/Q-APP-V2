"""Test for X-Request-Id middleware and CORS configuration."""

import os
import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_request_id_passthrough():
    """Test that X-Request-Id from request is passed through to response."""
    request_id = f"test_{uuid.uuid4()}"
    response = client.get("/api/v1/health", headers={"X-Request-Id": request_id})
    
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id") == request_id


def test_request_id_generation():
    """Test that X-Request-Id is generated when not provided."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-Id")
    assert request_id is not None
    assert len(request_id) > 0
    # Check it's a valid UUID
    try:
        uuid.UUID(request_id)
    except ValueError:
        assert False, f"Generated request ID is not a valid UUID: {request_id}"


def test_request_id_on_error_responses():
    """Test that X-Request-Id is included in error responses."""
    # Test 404 error
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    assert "X-Request-Id" in response.headers
    
    # Test with provided request ID
    request_id = f"test_{uuid.uuid4()}"
    response = client.get("/api/v1/nonexistent", headers={"X-Request-Id": request_id})
    assert response.status_code == 404
    assert response.headers.get("X-Request-Id") == request_id


def test_cors_allowed_origin():
    """Test CORS allows configured origins."""
    # Default is localhost:3000
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_disallowed_origin():
    """Test CORS blocks unconfigured origins."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # CORS middleware returns 400 for disallowed origins
    assert response.status_code == 400


def test_cors_with_environment_variable(monkeypatch):
    """Test CORS configuration from environment variable."""
    # Set multiple allowed origins
    test_origins = "http://localhost:3000,https://example.com,https://app.example.com"
    monkeypatch.setenv("CORS_ORIGINS", test_origins)
    
    # Need to reimport app to pick up the new environment variable
    import importlib
    import app.main
    importlib.reload(app.main)
    from app.main import app as reloaded_app
    
    test_client = TestClient(reloaded_app)
    
    # Test first origin
    response = test_client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_allowed_headers():
    """Test CORS allows required headers."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type,X-Request-Id"
        }
    )
    
    assert response.status_code == 200
    allowed_headers = response.headers.get("access-control-allow-headers", "")
    assert "authorization" in allowed_headers.lower()
    assert "content-type" in allowed_headers.lower()


def test_cors_allowed_methods():
    """Test CORS allows all HTTP methods."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "DELETE"
        }
    )
    
    assert response.status_code == 200
    allowed_methods = response.headers.get("access-control-allow-methods", "")
    assert "DELETE" in allowed_methods or "*" in allowed_methods


def test_cors_credentials():
    """Test CORS credentials configuration."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 200
    # Credentials should be allowed as per middleware configuration
    credentials = response.headers.get("access-control-allow-credentials", "")
    assert credentials.lower() == "true"