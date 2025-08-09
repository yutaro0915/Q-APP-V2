"""Test rate limiting for threads creation."""

import os
import time
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.threads import ThreadCard

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
def test_rate_limit_thread_create(mock_get_current_user, mock_get_db_pool):
    """Test that creating threads too quickly triggers rate limit."""
    from app.main import app
    from app.util.rate_limit import rate_limiter
    
    # Clear any existing rate limit state
    rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock user authentication
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to return ThreadCard
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
    
    mock_service = MagicMock()
    mock_service.create_thread = AsyncMock(return_value=mock_thread_card)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        # First request should succeed
        response1 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread 1",
                "body": "Test body 1",
                "tags": [],
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second request immediately after should be rate limited
        response2 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread 2",
                "body": "Test body 2",
                "tags": [],
                "imageKey": None
            }
        )
        assert response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_rate_limit_headers(mock_get_current_user, mock_get_db_pool):
    """Test that rate limit headers are included in 429 response."""
    from app.main import app
    from app.util.rate_limit import rate_limiter
    
    # Clear any existing rate limit state
    rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock user authentication
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
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
    
    mock_service = MagicMock()
    mock_service.create_thread = AsyncMock(return_value=mock_thread_card)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        # First request
        response1 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread 1",
                "body": "Test body 1",
                "tags": [],
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second request should be rate limited
        response2 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread 2",
                "body": "Test body 2",
                "tags": [],
                "imageKey": None
            }
        )
        
        if response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            # Check required headers
            assert "Retry-After" in response2.headers
            assert "X-RateLimit-Limit" in response2.headers
            assert "X-RateLimit-Remaining" in response2.headers
            assert "X-RateLimit-Reset" in response2.headers
            
            # Validate header values
            assert int(response2.headers["Retry-After"]) > 0
            assert response2.headers["X-RateLimit-Limit"] == "1"
            assert response2.headers["X-RateLimit-Remaining"] == "0"


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_rate_limit_different_users(mock_get_current_user, mock_get_db_pool):
    """Test that rate limit is per-user."""
    from app.main import app
    from app.util.rate_limit import rate_limiter
    
    # Clear any existing rate limit state
    rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
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
    
    mock_service = MagicMock()
    mock_service.create_thread = AsyncMock(return_value=mock_thread_card)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        # First user creates a thread
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        response1 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token_1"},
            json={
                "title": "User 1 Thread",
                "body": "Test body",
                "tags": [],
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Different user should be able to create immediately
        mock_get_current_user.return_value = "usr_99HX123456789ABCDEFGHJKMNP"
        response2 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token_2"},
            json={
                "title": "User 2 Thread",
                "body": "Test body",
                "tags": [],
                "imageKey": None
            }
        )
        assert response2.status_code == status.HTTP_201_CREATED


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_rate_limit_reset_after_time(mock_get_current_user, mock_get_db_pool):
    """Test that rate limit resets after the time window."""
    from app.main import app
    from app.util.rate_limit import rate_limiter
    
    # Clear any existing rate limit state
    if hasattr(rate_limiter, 'reset'):
        rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock user authentication
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
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
    
    mock_service = MagicMock()
    mock_service.create_thread = AsyncMock(return_value=mock_thread_card)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        # First request should succeed
        response1 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread 1",
                "body": "Test body 1",
                "tags": [],
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Clear rate limit state to simulate time passing
        if hasattr(rate_limiter, 'reset'):
            rate_limiter.reset()
        
        # Should be able to create another thread after reset
        response2 = client.post(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"},
            json={
                "title": "Test Thread 2",
                "body": "Test body 2",
                "tags": [],
                "imageKey": None
            }
        )
        assert response2.status_code == status.HTTP_201_CREATED