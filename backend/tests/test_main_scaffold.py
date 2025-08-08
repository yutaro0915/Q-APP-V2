import pytest
from fastapi.testclient import TestClient
import os
from unittest.mock import patch
import uuid


def test_x_request_id_header_generation():
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    
    request_id = response.headers["x-request-id"]
    assert len(request_id) == 36
    try:
        uuid.UUID(request_id)
    except ValueError:
        pytest.fail("X-Request-Id is not a valid UUID")


def test_x_request_id_passthrough():
    from app.main import app
    client = TestClient(app)
    
    custom_id = str(uuid.uuid4())
    response = client.get("/api/v1/health", headers={"X-Request-Id": custom_id})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id


def test_cors_from_environment():
    with patch.dict(os.environ, {"CORS_ORIGINS": "http://example.com,https://app.example.com"}):
        import importlib
        import app.main
        importlib.reload(app.main)
        from app.main import app
        
        client = TestClient(app)
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://example.com"


def test_cors_default_localhost():
    with patch.dict(os.environ, {}, clear=True):
        if "CORS_ORIGINS" in os.environ:
            del os.environ["CORS_ORIGINS"]
        
        import importlib
        import app.main
        importlib.reload(app.main)
        from app.main import app
        
        client = TestClient(app)
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_error_handling_404():
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/nonexistent")
    assert response.status_code == 404
    assert "x-request-id" in response.headers
    
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Resource not found"


def test_error_handling_500():
    from app.main import app
    from fastapi import HTTPException
    client = TestClient(app)
    
    @app.get("/api/v1/test-error")
    async def test_error():
        raise HTTPException(status_code=500, detail="Internal server error")
    
    response = client.get("/api/v1/test-error")
    assert response.status_code == 500
    assert "x-request-id" in response.headers


def test_request_logging(caplog):
    from app.main import app
    client = TestClient(app)
    
    with caplog.at_level("INFO"):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    assert any("method=GET" in record.message and "path=/api/v1/health" in record.message for record in caplog.records)
    assert any("status=200" in record.message for record in caplog.records)


def test_api_prefix():
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 404
    
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_openapi_docs_available():
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Kyudai Campus SNS API"
    assert data["info"]["version"] == "1.0.0"