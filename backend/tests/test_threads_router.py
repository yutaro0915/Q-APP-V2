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


@patch('app.core.db.get_db_pool')
def test_list_threads_without_auth(mock_get_db_pool):
    """Test listing threads without authentication."""
    from app.main import app
    from app.schemas.threads import PaginatedThreadCards, ThreadCard
    client = TestClient(app)
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to return paginated threads
    mock_threads = PaginatedThreadCards(
        items=[
            ThreadCard(
                id="thr_01HX123456789ABCDEFGHJKMNP",
                title="Test Thread 1",
                excerpt="Test body 1",
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
        ],
        nextCursor=None
    )
    
    mock_service = MagicMock()
    mock_service.list_threads_new = AsyncMock(return_value=mock_threads)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.get("/api/v1/threads")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "thr_01HX123456789ABCDEFGHJKMNP"


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_list_threads_with_auth(mock_get_current_user, mock_get_db_pool):
    """Test listing threads with authentication."""
    from app.main import app
    from app.schemas.threads import PaginatedThreadCards, ThreadCard
    client = TestClient(app)
    
    # Mock get_current_user
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to return paginated threads with is_mine
    mock_threads = PaginatedThreadCards(
        items=[
            ThreadCard(
                id="thr_01HX123456789ABCDEFGHJKMNP",
                title="My Thread",
                excerpt="My content",
                tags=[],
                heat=0,
                replies=0,
                saves=0,
                createdAt="2024-01-01T00:00:00Z",
                lastReplyAt=None,
                hasImage=False,
                imageThumbUrl=None,
                solved=False,
                authorAffiliation=None,
                isMine=True
            )
        ],
        nextCursor="eyJ2IjoxLCJkIjoiMjAyNC0wMS0wMVQwMDowMDowMFoiLCJpZCI6InRocl8wMUhYMTIzNDU2Nzg5MEFCQ0RFRkdISktNTlAifQ"
    )
    
    mock_service = MagicMock()
    mock_service.list_threads_new = AsyncMock(return_value=mock_threads)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.get(
            "/api/v1/threads",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert data["items"][0]["isMine"] is True
        assert data["nextCursor"] is not None


@patch('app.core.db.get_db_pool')
def test_list_threads_with_cursor(mock_get_db_pool):
    """Test listing threads with cursor pagination."""
    from app.main import app
    from app.schemas.threads import PaginatedThreadCards
    client = TestClient(app)
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service
    mock_threads = PaginatedThreadCards(items=[], nextCursor=None)
    mock_service = MagicMock()
    mock_service.list_threads_new = AsyncMock(return_value=mock_threads)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        cursor = "eyJ2IjoxLCJkIjoiMjAyNC0wMS0wMVQwMDowMDowMFoiLCJpZCI6InRocl8wMUhYMTIzNDU2Nzg5MEFCQ0RFRkdISktNTlAifQ"
        response = client.get(f"/api/v1/threads?cursor={cursor}")
        
        assert response.status_code == status.HTTP_200_OK
        # Verify service was called with cursor
        mock_service.list_threads_new.assert_called_once()
        call_args = mock_service.list_threads_new.call_args
        assert call_args.kwargs["cursor"] == cursor


@patch('app.core.db.get_db_pool')
def test_list_threads_with_sort_hot(mock_get_db_pool):
    """Test listing threads with sort=hot."""
    from app.main import app
    client = TestClient(app)
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # For Phase 1, hot sorting is not implemented, should return 400
    response = client.get("/api/v1/threads?sort=hot")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@patch('app.core.db.get_db_pool')
def test_get_thread_detail(mock_get_db_pool):
    """Test getting thread detail."""
    from app.main import app
    from app.schemas.threads import ThreadDetail
    client = TestClient(app)
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to return thread detail
    mock_thread = ThreadDetail(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        title="Test Thread",
        body="Test body content",
        tags=[],
        upCount=5,
        saveCount=2,
        createdAt="2024-01-01T00:00:00Z",
        lastActivityAt="2024-01-01T00:00:00Z",
        solvedCommentId=None,
        hasImage=False,
        imageUrl=None,
        authorAffiliation=None
    )
    
    mock_service = MagicMock()
    mock_service.get_thread = AsyncMock(return_value=mock_thread)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.get("/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "thr_01HX123456789ABCDEFGHJKMNP"
        assert data["title"] == "Test Thread"
        assert data["body"] == "Test body content"


@patch('app.core.db.get_db_pool')
@patch('app.routers.threads.get_current_user')
def test_get_thread_detail_with_auth(mock_get_current_user, mock_get_db_pool):
    """Test getting thread detail with authentication."""
    from app.main import app
    from app.schemas.threads import ThreadDetail
    client = TestClient(app)
    
    # Mock get_current_user
    mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to return thread detail with isMine
    mock_thread = ThreadDetail(
        id="thr_01HX123456789ABCDEFGHJKMNP",
        title="My Thread",
        body="My content",
        tags=[],
        upCount=0,
        saveCount=0,
        createdAt="2024-01-01T00:00:00Z",
        lastActivityAt="2024-01-01T00:00:00Z",
        solvedCommentId=None,
        hasImage=False,
        imageUrl=None,
        authorAffiliation=None,
        isMine=True
    )
    
    mock_service = MagicMock()
    mock_service.get_thread = AsyncMock(return_value=mock_thread)
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.get(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["isMine"] is True


@patch('app.core.db.get_db_pool')
def test_get_thread_not_found(mock_get_db_pool):
    """Test getting non-existent thread returns 404."""
    from app.main import app
    from app.util.errors import NotFoundException
    client = TestClient(app)
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to raise NotFoundException
    mock_service = MagicMock()
    mock_service.get_thread = AsyncMock(side_effect=NotFoundException("Thread not found"))
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.get("/api/v1/threads/thr_99HX123456789ABCDEFGHJKMNP")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"


@patch('app.core.db.get_db_pool')
def test_get_thread_invalid_id(mock_get_db_pool):
    """Test getting thread with invalid ID format returns 400."""
    from app.main import app
    from app.util.errors import ValidationException
    client = TestClient(app)
    
    # Mock database pool and connection
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool.acquire.return_value = MockAcquire(mock_conn)
    mock_get_db_pool.return_value = mock_pool
    
    # Mock service to raise ValidationException
    mock_service = MagicMock()
    mock_service.get_thread = AsyncMock(side_effect=ValidationException("Invalid thread ID"))
    
    with patch('app.routers.threads.ThreadService', return_value=mock_service):
        response = client.get("/api/v1/threads/invalid-id")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"