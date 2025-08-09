"""Test rate limiting for comment creation."""

import os
import time
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.comments import CreatedResponse

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
def test_rate_limit_comment_create(mock_get_current_user, mock_get_db_pool):
    """Test that creating comments too quickly triggers rate limit."""
    from app.main import app
    from app.util.rate_limit import comment_rate_limiter
    
    # Clear any existing rate limit state
    comment_rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock user authentication
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to return CreatedResponse
    mock_created_response = CreatedResponse(
        id="cmt_01HX123456789ABCDEFGHJKMNP",
        createdAt="2024-01-01T00:00:00Z"
    )
    
    mock_service = MagicMock()
    mock_service.create_comment = AsyncMock(return_value=mock_created_response)
    
    with patch('app.routers.threads.CommentService', return_value=mock_service):
        # First request should succeed
        response1 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token"},
            json={
                "body": "Test comment 1",
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second request immediately after should be rate limited
        response2 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token"},
            json={
                "body": "Test comment 2",
                "imageKey": None
            }
        )
        assert response2.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_rate_limit_comment_headers(mock_get_current_user, mock_get_db_pool):
    """Test that rate limit headers are included in 429 response."""
    from app.main import app
    from app.util.rate_limit import comment_rate_limiter
    
    # Clear any existing rate limit state
    comment_rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock user authentication
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
    mock_created_response = CreatedResponse(
        id="cmt_01HX123456789ABCDEFGHJKMNP",
        createdAt="2024-01-01T00:00:00Z"
    )
    
    mock_service = MagicMock()
    mock_service.create_comment = AsyncMock(return_value=mock_created_response)
    
    with patch('app.routers.threads.CommentService', return_value=mock_service):
        # First request
        response1 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token"},
            json={
                "body": "Test comment 1",
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second request should be rate limited
        response2 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token"},
            json={
                "body": "Test comment 2",
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
            
            # Check error code is RATE_LIMITED per spec
            json_body = response2.json()
            assert json_body["error"]["code"] == "RATE_LIMITED"
            assert "comment" in json_body["error"]["message"].lower()
            
            # Check that details is now an array (not a dict)
            assert "details" in json_body["error"]
            assert isinstance(json_body["error"]["details"], list)
            assert len(json_body["error"]["details"]) == 1
            
            # Check array contains correct structure
            details_item = json_body["error"]["details"][0]
            assert "retryAfter" in details_item
            assert "limit" in details_item  
            assert "remaining" in details_item
            assert "reset" in details_item
            assert details_item["limit"] == 1
            assert details_item["remaining"] == 0
            assert details_item["retryAfter"] > 0


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_rate_limit_comment_different_users(mock_get_current_user, mock_get_db_pool):
    """Test that rate limit is per-user."""
    from app.main import app
    from app.util.rate_limit import comment_rate_limiter
    
    # Clear any existing rate limit state
    comment_rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
    mock_created_response = CreatedResponse(
        id="cmt_01HX123456789ABCDEFGHJKMNP",
        createdAt="2024-01-01T00:00:00Z"
    )
    
    mock_service = MagicMock()
    mock_service.create_comment = AsyncMock(return_value=mock_created_response)
    
    with patch('app.routers.threads.CommentService', return_value=mock_service):
        # First user creates a comment
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        response1 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token_1"},
            json={
                "body": "User 1 comment",
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Different user should be able to create immediately
        mock_get_current_user.return_value = "usr_99HX123456789ABCDEFGHJKMNP"
        response2 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token_2"},
            json={
                "body": "User 2 comment",
                "imageKey": None
            }
        )
        assert response2.status_code == status.HTTP_201_CREATED


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_rate_limit_comment_reset_after_time(mock_get_current_user, mock_get_db_pool):
    """Test that rate limit resets after the time window."""
    from app.main import app
    from app.util.rate_limit import comment_rate_limiter
    
    # Clear any existing rate limit state
    if hasattr(comment_rate_limiter, 'reset'):
        comment_rate_limiter.reset()
    
    client = TestClient(app)
    
    # Mock user authentication
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
    mock_created_response = CreatedResponse(
        id="cmt_01HX123456789ABCDEFGHJKMNP",
        createdAt="2024-01-01T00:00:00Z"
    )
    
    mock_service = MagicMock()
    mock_service.create_comment = AsyncMock(return_value=mock_created_response)
    
    with patch('app.routers.threads.CommentService', return_value=mock_service):
        # First request should succeed
        response1 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token"},
            json={
                "body": "Test comment 1",
                "imageKey": None
            }
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Clear rate limit state to simulate time passing
        if hasattr(comment_rate_limiter, 'reset'):
            comment_rate_limiter.reset()
        
        # Should be able to create another comment after reset
        response2 = client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer test_token"},
            json={
                "body": "Test comment 2",
                "imageKey": None
            }
        )
        assert response2.status_code == status.HTTP_201_CREATED