from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_x_request_id_echoes_back_when_provided():
    req_id = "test-req-123"
    response = client.get("/api/v1/health", headers={"X-Request-Id": req_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id") == req_id


def test_x_request_id_is_generated_when_missing():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    value = response.headers.get("X-Request-Id")
    assert value is not None and len(value) > 0


def test_cors_preflight_is_rejected_for_disallowed_origin():
    # origin not in allowed list should be rejected for preflight
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Starlette CORS returns 400 for invalid preflight
    assert response.status_code == 400

