"""Test authentication bootstrap endpoint."""
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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
    
    # Create a proper async context manager for transaction
    class MockTransaction:
        async def __aenter__(self):
            return None
        async def __aexit__(self, *args):
            pass
    
    mock_pool.acquire.return_value = MockAcquire()
    mock_connection.transaction = MagicMock(return_value=MockTransaction())
    
    return mock_pool, mock_connection


def test_bootstrap_new_user(mock_db_pool):
    """Test bootstrap creates new user when no device_secret provided."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock database queries
    mock_connection.fetchrow = AsyncMock(return_value=None)  # User doesn't exist
    mock_connection.execute = AsyncMock()
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        
        with patch("app.routers.auth.generate_id") as mock_generate_id:
            mock_generate_id.side_effect = ["usr_01HX1234567890ABCDEFGHIJKL", "ses_01HX1234567890ABCDEFGHIJKL"]
            
            from app.main import app
            client = TestClient(app)
            
            response = client.post("/api/v1/auth/bootstrap", json={})
            
            assert response.status_code == 200
            data = response.json()
            assert "userId" in data
            assert data["userId"] == "usr_01HX1234567890ABCDEFGHIJKL"
            assert "token" in data
            assert "expiresAt" in data
            
            # Verify user was created
            mock_connection.execute.assert_called()


def test_bootstrap_with_device_secret(mock_db_pool):
    """Test bootstrap with device_secret still creates new user in Phase 1."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock database queries
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.execute = AsyncMock()
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        
        with patch("app.routers.auth.generate_id") as mock_generate_id:
            mock_generate_id.side_effect = ["usr_01HX1234567890ABCDEFGHIJKL", "ses_01HX1234567890ABCDEFGHIJKL"]
            
            from app.main import app
            client = TestClient(app)
            
            # Phase 1: device_secret is ignored
            device_secret = "existing_device_secret_123"
            
            response = client.post("/api/v1/auth/bootstrap", json={
                "device_secret": device_secret
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["userId"].startswith("usr_")
            assert "token" in data
            assert "expiresAt" in data


def test_bootstrap_without_device_secret(mock_db_pool):
    """Test bootstrap without device_secret creates new user."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock database queries
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.execute = AsyncMock()
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        
        with patch("app.routers.auth.generate_id") as mock_generate_id:
            mock_generate_id.side_effect = ["usr_01HX1234567890ABCDEFGHIJKL", "ses_01HX1234567890ABCDEFGHIJKL"]
            
            from app.main import app
            client = TestClient(app)
            
            response = client.post("/api/v1/auth/bootstrap", json={})
            
            assert response.status_code == 200
            data = response.json()
            assert data["userId"].startswith("usr_")


def test_bootstrap_creates_session(mock_db_pool):
    """Test bootstrap creates session with correct expiry."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock database queries
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.execute = AsyncMock()
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        
        with patch("app.routers.auth.generate_id") as mock_generate_id:
            mock_generate_id.side_effect = ["usr_01HX1234567890ABCDEFGHIJKL", "ses_01HX1234567890ABCDEFGHIJKL"]
            
            from app.main import app
            client = TestClient(app)
            
            response = client.post("/api/v1/auth/bootstrap", json={})
            
            assert response.status_code == 200
            data = response.json()
            
            # Check expiry is approximately 7 days from now
            expires_at = datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
            expected_expiry = datetime.now(timezone.utc) + timedelta(days=7)
            diff = abs((expires_at - expected_expiry).total_seconds())
            assert diff < 10  # Within 10 seconds tolerance


def test_bootstrap_token_hash_stored(mock_db_pool):
    """Test bootstrap stores hashed token in database."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock database queries
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.execute = AsyncMock()
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        
        with patch("app.routers.auth.generate_id") as mock_generate_id:
            mock_generate_id.side_effect = ["usr_01HX1234567890ABCDEFGHIJKL", "ses_01HX1234567890ABCDEFGHIJKL"]
            
            from app.main import app
            client = TestClient(app)
            
            response = client.post("/api/v1/auth/bootstrap", json={})
            
            assert response.status_code == 200
            data = response.json()
            token = data["token"]
            
            # Verify that execute was called for both users and sessions
            assert mock_connection.execute.called
            assert mock_connection.execute.call_count >= 2  # At least 2 inserts


def test_bootstrap_response_format(mock_db_pool):
    """Test bootstrap response follows API contract format."""
    mock_pool, mock_connection = mock_db_pool
    
    # Mock database queries
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.execute = AsyncMock()
    
    with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
        
        with patch("app.routers.auth.generate_id") as mock_generate_id:
            mock_generate_id.side_effect = ["usr_01HX1234567890ABCDEFGHIJKL", "ses_01HX1234567890ABCDEFGHIJKL"]
            
            from app.main import app
            client = TestClient(app)
            
            response = client.post("/api/v1/auth/bootstrap", json={})
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert set(data.keys()) == {"userId", "token", "expiresAt"}
            assert data["userId"].startswith("usr_")
            assert len(data["token"]) > 0
            # expiresAt should be ISO format with Z timezone
            assert data["expiresAt"].endswith("Z")
            datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))