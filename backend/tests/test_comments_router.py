"""Tests for comments router."""

import os
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# Set DATABASE_URL for testing
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"

from app.main import app


class MockAcquire:
    """Mock async context manager for pool.acquire()."""
    def __init__(self, connection):
        self.connection = connection
    
    async def __aenter__(self):
        return self.connection
    
    async def __aexit__(self, *args):
        pass


class TestCommentsRouter:
    """Test class for comments router endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_delete_comment_endpoint_exists(self):
        """Test that DELETE /comments/{comment_id} endpoint exists."""
        # This will fail initially because the endpoint doesn't exist
        response = self.client.delete("/comments/cmt_01HX123456789ABCDEFGHJKMNP")
        # Should not return 404 for unknown endpoint, but for missing auth
        assert response.status_code != 404 or response.json().get("detail") != "Not Found"

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.comments.get_current_user')
    def test_delete_comment_success(self, mock_get_current_user, mock_get_db_pool):
        """Test successful comment deletion by owner."""
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service
        with patch('app.services.comments_service.CommentService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_comment = AsyncMock()  # Success - no exception
            
            response = self.client.delete(
                "/api/v1/comments/cmt_01HX123456789ABCDEFGHJKMNP",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Should return 204 No Content
            assert response.status_code == 204
            assert response.content == b""

    def test_delete_comment_unauthorized(self):
        """Test comment deletion without authentication."""
        response = self.client.delete("/api/v1/comments/cmt_01HX123456789ABCDEFGHJKMNP")
        
        # Should return 400 for missing authorization header
        assert response.status_code == 400

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.comments.get_current_user')
    def test_delete_comment_not_found(self, mock_get_current_user, mock_get_db_pool):
        """Test deletion of non-existent comment."""
        from app.util.errors import NotFoundException
        
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to raise NotFoundException
        with patch('app.services.comments_service.CommentService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_comment = AsyncMock(side_effect=NotFoundException("Comment not found"))
            
            response = self.client.delete(
                "/api/v1/comments/cmt_nonexistent",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Should return 404 Not Found
            assert response.status_code == 404
            error_data = response.json()
            assert "not found" in error_data["error"]["message"].lower()

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.comments.get_current_user')
    def test_delete_comment_forbidden(self, mock_get_current_user, mock_get_db_pool):
        """Test deletion of someone else's comment (should return 404 for security)."""
        from app.util.errors import NotFoundException
        
        # Mock authentication to return different user ID
        mock_get_current_user.return_value = "usr_different_user"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to raise NotFoundException (service treats unauthorized as not found)
        with patch('app.services.comments_service.CommentService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.delete_comment = AsyncMock(side_effect=NotFoundException("Comment not found"))
            
            response = self.client.delete(
                "/api/v1/comments/cmt_01HX123456789ABCDEFGHJKMNP",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Should return 404 Not Found (not 403 for security)
            assert response.status_code == 404
            error_data = response.json()
            assert "not found" in error_data["error"]["message"].lower()

    def test_delete_comment_invalid_id_format(self):
        """Test deletion with invalid comment ID format."""
        response = self.client.delete(
            "/api/v1/comments/invalid_id",
            headers={"Authorization": "Bearer valid_token"}
        )
        
        # Should return validation error or 404
        assert response.status_code in [400, 404, 422]

    def test_post_comment_endpoint_exists(self):
        """Test that POST /threads/{id}/comments endpoint exists."""
        # This will fail initially because the endpoint doesn't exist
        response = self.client.post("/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments")
        # Should not return 404 for unknown endpoint, but for missing auth or data
        assert response.status_code != 404 or response.json().get("detail") != "Not Found"

    @patch('app.services.comments_service.CommentService.create_comment')
    @patch('app.routers.threads.get_current_user')
    def test_post_comment_success(self, mock_get_current_user, mock_create_comment):
        """Test successful comment creation."""
        from app.schemas.comments import CreatedResponse
        
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock service to return CreatedResponse
        mock_created_response = CreatedResponse(
            id="cmt_01HX123456789ABCDEFGHJKMNP",
            createdAt="2024-01-01T00:00:00Z"
        )
        mock_create_comment.return_value = mock_created_response
        
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer valid_token"},
            json={"body": "This is a test comment", "imageKey": None}
        )
        
        # Should return 201 Created
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "cmt_01HX123456789ABCDEFGHJKMNP"
        assert data["createdAt"] == "2024-01-01T00:00:00Z"
        
        # Verify service was called with correct parameters
        mock_create_comment.assert_called_once()
        call_args = mock_create_comment.call_args
        assert call_args.kwargs["user_id"] == "usr_01HX123456789ABCDEFGHJKMNP"
        assert call_args.kwargs["thread_id"] == "thr_01HX123456789ABCDEFGHJKMNP"
        assert call_args.kwargs["dto"].body == "This is a test comment"

    def test_post_comment_unauthorized(self):
        """Test comment creation without authentication."""
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            json={"body": "This is a test comment", "imageKey": None}
        )
        
        # Should return 400 for missing authorization header
        assert response.status_code == 400

    def test_post_comment_invalid_data(self):
        """Test comment creation with invalid data."""
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer valid_token"},
            json={"imageKey": None}  # Missing body
        )
        
        # Should return validation error
        assert response.status_code == 400

    def test_post_comment_empty_body(self):
        """Test comment creation with empty body."""
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/comments",
            headers={"Authorization": "Bearer valid_token"},
            json={"body": "", "imageKey": None}
        )
        
        # Should return validation error
        assert response.status_code == 400

    @patch('app.services.comments_service.CommentService.create_comment')
    @patch('app.routers.threads.get_current_user')
    def test_post_comment_thread_not_found(self, mock_get_current_user, mock_create_comment):
        """Test comment creation on non-existent thread."""
        from app.util.errors import NotFoundException
        
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock service to raise NotFoundException
        mock_create_comment.side_effect = NotFoundException("Thread not found")
        
        response = self.client.post(
            "/api/v1/threads/thr_nonexistent/comments",
            headers={"Authorization": "Bearer valid_token"},
            json={"body": "This is a test comment", "imageKey": None}
        )
        
        # Should return 404 Not Found
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["error"]["message"].lower()