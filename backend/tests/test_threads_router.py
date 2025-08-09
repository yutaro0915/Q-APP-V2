"""Test threads router."""

import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.threads import ThreadCard, AuthorAffiliation

# Set DATABASE_URL for testing
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"


class MockAcquire:
    """Mock async context manager for pool.acquire()."""
    def __init__(self, connection):
        self.connection = connection
    
    async def __aenter__(self):
        return self.connection
    
    async def __aexit__(self, *args):
        pass


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_create_thread_authenticated(mock_get_current_user, mock_get_db_pool):
    """Test creating thread with authentication."""
    # Import here to avoid circular imports
    from app.main import app
    client = TestClient(app)
    
    # Mock service to return ThreadCard object
    mock_thread_card = ThreadCard(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        title="Test Thread",
        excerpt="Test body content",
        tags=[],
        heat=0,
        replies=0,
        saves=0,
        createdAt="2024-01-01T00:00:00Z",
        lastReplyAt=None,
        hasImage=False,
        imageThumbUrl=None,
        solved=False,
        authorAffiliation=None
    )
    
    # Setup mock get_current_user
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock the database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
    mock_service = MagicMock()
    mock_service.create_thread = AsyncMock(return_value=mock_thread_card)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread",
                "body": "Test body content",
                "tags": [],
                "imageKey": None
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["id"] == "thr_01HX123456789ABCDEFGHJKMNP"
        assert "createdAt" in data
        assert data["createdAt"] == "2024-01-01T00:00:00Z"
        
        # Verify service was called
        mock_service.create_thread.assert_called_once()


@patch('app.routers.threads.get_current_user')
def test_create_thread_unauthenticated(mock_get_current_user):
    """Test creating thread without authentication."""
    from app.main import app
    from app.util.errors import UnauthorizedException
    client = TestClient(app)
    
    # Mock get_current_user to raise UnauthorizedException
    mock_get_current_user.side_effect = UnauthorizedException("Invalid or expired session")
    
    response = client.post(
        "/api/v1/threads",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "title": "Test Thread",
            "body": "Test body content",
            "tags": [],
            "imageKey": None
        }
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


@patch('app.routers.threads.get_current_user')
def test_create_thread_invalid_data(mock_get_current_user):
    """Test creating thread with invalid data."""
    from app.main import app
    client = TestClient(app)
    
    # Mock get_current_user to return user_id
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Missing title
    response = client.post(
        "/api/v1/threads",
        headers={"Authorization": "Bearer test_token"},
        json={
            "body": "Test body content",
            "tags": [],
            "imageKey": None
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch('app.routers.threads.get_current_user')
def test_create_thread_empty_title(mock_get_current_user):
    """Test creating thread with empty title."""
    from app.main import app
    client = TestClient(app)
    
    # Mock get_current_user to return user_id
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    response = client.post(
        "/api/v1/threads",
        headers={"Authorization": "Bearer test_token"},
        json={
            "title": "",
            "body": "Test body content",
            "tags": [],
            "imageKey": None
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch('app.routers.threads.get_current_user')
def test_create_thread_title_too_long(mock_get_current_user):
    """Test creating thread with title too long."""
    from app.main import app
    client = TestClient(app)
    
    # Mock get_current_user to return user_id
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    response = client.post(
        "/api/v1/threads",
        headers={"Authorization": "Bearer test_token"},
        json={
            "title": "a" * 61,  # Max is 60
            "body": "Test body content",
            "tags": [],
            "imageKey": None
        }
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_create_thread_with_tags(mock_get_current_user, mock_get_db_pool):
    """Test creating thread with tags."""
    from app.main import app
    client = TestClient(app)
    
    # Mock get_current_user to return user_id
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock ThreadCard object
    mock_thread_card = ThreadCard(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        title="Test Thread",
        excerpt="Test body content",
        tags=[{"key": "種別", "value": "question"}],
        heat=0,
        replies=0,
        saves=0,
        createdAt="2024-01-01T00:00:00Z",
        lastReplyAt=None,
        hasImage=False,
        imageThumbUrl=None,
        solved=False,
        authorAffiliation=None
    )
    
    # Mock the database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
    mock_service = MagicMock()
    mock_service.create_thread = AsyncMock(return_value=mock_thread_card)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread",
                "body": "Test body content",
                "tags": [{"key": "種別", "value": "question"}],
                "imageKey": None
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == "thr_01HX123456789ABCDEFGHJKMNP"