from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_x_request_id_header():
    """X-Request-Idヘッダーが生成されることを確認"""
    response = client.get("/api/v1/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0

def test_cors_headers():
    """CORS設定が適用されることを確認"""
    response = client.options("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_openapi_docs():
    """OpenAPIドキュメントが生成されることを確認"""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    assert openapi["info"]["title"] == "Kyudai Campus SNS API"
    assert openapi["info"]["version"] == "1.0.0"