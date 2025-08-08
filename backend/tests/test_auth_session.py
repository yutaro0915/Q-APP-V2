"""Test authentication session endpoint."""
import hashlib
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Set environment variable for testing
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"


@pytest.fixture
def mock_db_pool():
    """Mock database pool."""
    mock_pool = MagicMock()
    mock_connection = AsyncMock()
    
    # Create a proper async context manager for acquire
    class MockAcquire:
        async def __aenter__(self):
            return mock_connection
        async def __aexit__(self, *args):
            pass
    
    mock_pool.acquire.return_value = MockAcquire()
    
    return mock_pool, mock_connection


def test_get_current_user_with_valid_token(mock_db_pool):
    """Test get_current_user dependency with valid token."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock valid session in database
    token = "valid_test_token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    mock_connection.fetchrow = AsyncMock(return_value={
        "user_id": "usr_01HX1234567890ABCDEFGHIJKL",
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1)  # Valid session
    })
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        from app.routers.auth import get_current_user
        
        async def run_test():
            result = await get_current_user(f"Bearer {token}")
            assert result == "usr_01HX1234567890ABCDEFGHIJKL"
            
            # Verify query was called with correct token hash
            mock_connection.fetchrow.assert_called_once()
            call_args = mock_connection.fetchrow.call_args
            assert token_hash in str(call_args)
        
        import asyncio
        asyncio.run(run_test())


def test_get_current_user_with_invalid_token(mock_db_pool):
    """Test get_current_user dependency with invalid token."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock no session found in database
    mock_connection.fetchrow = AsyncMock(return_value=None)
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        from app.routers.auth import get_current_user
        
        async def run_test():
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("Bearer invalid_token")
            
            assert exc_info.value.status_code == 401
            assert "Invalid or expired session" in str(exc_info.value.detail)
        
        import asyncio
        asyncio.run(run_test())


def test_get_current_user_with_expired_token(mock_db_pool):
    """Test get_current_user dependency with expired token."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock expired session in database
    mock_connection.fetchrow = AsyncMock(return_value={
        "user_id": "usr_01HX1234567890ABCDEFGHIJKL",
        "expires_at": datetime.now(timezone.utc) - timedelta(days=1)  # Expired session
    })
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        from app.routers.auth import get_current_user
        
        async def run_test():
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user("Bearer expired_token")
            
            assert exc_info.value.status_code == 401
            assert "Invalid or expired session" in str(exc_info.value.detail)
        
        import asyncio
        asyncio.run(run_test())


def test_get_current_user_without_bearer_prefix():
    """Test get_current_user dependency without Bearer prefix."""
    from app.routers.auth import get_current_user
    
    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid_format_token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header" in str(exc_info.value.detail)
    
    import asyncio
    asyncio.run(run_test())


def test_session_endpoint_with_valid_token(mock_db_pool):
    """Test session endpoint with valid token."""
    mock_pool, mock_connection = mock_db_pool
    
    token = "valid_session_token"
    user_id = "usr_01HX1234567890ABCDEFGHIJKL"
    
    # Mock valid session
    mock_connection.fetchrow = AsyncMock(return_value={
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1)
    })
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/auth/session", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["userId"] == user_id


def test_session_endpoint_with_invalid_token(mock_db_pool):
    """Test session endpoint with invalid token."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock no session found
    mock_connection.fetchrow = AsyncMock(return_value=None)
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/auth/session", headers={
            "Authorization": "Bearer invalid_token"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"


def test_session_endpoint_without_token():
    """Test session endpoint without authorization header."""
    from app.main import app
    client = TestClient(app)
    
    response = client.get("/api/v1/auth/session")
    
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_session_endpoint_with_expired_token(mock_db_pool):
    """Test session endpoint with expired token."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock expired session
    mock_connection.fetchrow = AsyncMock(return_value={
        "user_id": "usr_01HX1234567890ABCDEFGHIJKL",
        "expires_at": datetime.now(timezone.utc) - timedelta(days=1)
    })
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        from app.main import app
        client = TestClient(app)
        
        response = client.get("/api/v1/auth/session", headers={
            "Authorization": "Bearer expired_token"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"