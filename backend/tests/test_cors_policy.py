from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_credentials_false():
    """CORS allow_credentials が False に設定されていることを確認"""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
    )
    
    assert response.status_code == 200
    # allow_credentials=False の場合、このヘッダーは含まれない
    assert "Access-Control-Allow-Credentials" not in response.headers


def test_cors_allowed_origin():
    """許可されたOriginがAccess-Control-Allow-Originに反映されることを確認"""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def test_cors_disallowed_origin():
    """許可されていないOriginが拒否されることを確認"""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://malicious.example.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 400
    # 許可されていないOriginの場合、Access-Control-Allow-Originヘッダーは含まれない
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_allows_authorization_header():
    """AuthorizationヘッダーがCORSで許可されることを確認"""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type"
        }
    )
    
    assert response.status_code == 200
    allow_headers = response.headers.get("Access-Control-Allow-Headers", "")
    # * または明示的にAuthorizationとContent-Typeが含まれることを確認
    assert allow_headers == "*" or ("Authorization" in allow_headers and "Content-Type" in allow_headers)