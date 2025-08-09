"""Tests for solve router."""

import os
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


class TestSolveRouter:
    """Test class for solve router endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_solve_endpoint_exists(self):
        """Test that POST /threads/{id}/solve endpoint exists."""
        response = self.client.post("/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve")
        # Should not return 404 for unknown endpoint, but for missing auth or data
        assert response.status_code != 404 or response.json().get("detail") != "Not Found"

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    @patch('app.services.solve_service.SolveService.set_solved_comment')
    def test_post_solve_set_success(self, mock_set_solved, mock_get_current_user, mock_get_db_pool):
        """Test successful solve setting with commentId."""
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to succeed (no exception)
        mock_set_solved.return_value = None
        
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": "cmt_01HX123456789ABCDEFGHJKMNP"}
        )
        
        # Should return 204 No Content
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify service was called with correct parameters
        mock_set_solved.assert_called_once()
        call_args = mock_set_solved.call_args
        assert call_args.kwargs["user_id"] == "usr_01HX123456789ABCDEFGHJKMNP"
        assert call_args.kwargs["thread_id"] == "thr_01HX123456789ABCDEFGHJKMNP"
        assert call_args.kwargs["comment_id"] == "cmt_01HX123456789ABCDEFGHJKMNP"

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    @patch('app.services.solve_service.SolveService.clear_solved_comment')
    def test_post_solve_clear_success(self, mock_clear_solved, mock_get_current_user, mock_get_db_pool):
        """Test successful solve clearing with null commentId."""
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to succeed (no exception)
        mock_clear_solved.return_value = None
        
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": None}
        )
        
        # Should return 204 No Content
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify service was called with correct parameters
        mock_clear_solved.assert_called_once()
        call_args = mock_clear_solved.call_args
        assert call_args.kwargs["user_id"] == "usr_01HX123456789ABCDEFGHJKMNP"
        assert call_args.kwargs["thread_id"] == "thr_01HX123456789ABCDEFGHJKMNP"

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    @patch('app.services.solve_service.SolveService.clear_solved_comment')
    def test_post_solve_clear_missing_commentid(self, mock_clear_solved, mock_get_current_user, mock_get_db_pool):
        """Test successful solve clearing with missing commentId field."""
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to succeed (no exception)
        mock_clear_solved.return_value = None
        
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={}  # Missing commentId field
        )
        
        # Should return 204 No Content (treats missing as null)
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify service was called
        mock_clear_solved.assert_called_once()

    def test_post_solve_unauthorized(self):
        """Test solve operation without authentication."""
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            json={"commentId": "cmt_01HX123456789ABCDEFGHJKMNP"}
        )
        
        # Should return 400 for missing authorization header
        assert response.status_code == 400

    def test_post_solve_invalid_json(self):
        """Test solve operation with invalid JSON."""
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            data="invalid json"
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    @patch('app.services.solve_service.SolveService.set_solved_comment')
    def test_post_solve_thread_not_found(self, mock_set_solved, mock_get_current_user, mock_get_db_pool):
        """Test solve operation on non-existent thread."""
        from app.util.errors import NotFoundException
        
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to raise NotFoundException
        mock_set_solved.side_effect = NotFoundException("Thread not found")
        
        response = self.client.post(
            "/api/v1/threads/thr_NONEXISTENT/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": "cmt_01HX123456789ABCDEFGHJKMNP"}
        )
        
        # Should return 404 Not Found
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["error"]["message"].lower()

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    @patch('app.services.solve_service.SolveService.set_solved_comment')
    def test_post_solve_forbidden(self, mock_set_solved, mock_get_current_user, mock_get_db_pool):
        """Test solve operation by non-owner of thread."""
        from app.util.errors import ForbiddenException
        
        # Mock authentication to return different user ID
        mock_get_current_user.return_value = "usr_DIFFERENT_USER"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to raise ForbiddenException
        mock_set_solved.side_effect = ForbiddenException("Only thread author can set solved comment")
        
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": "cmt_01HX123456789ABCDEFGHJKMNP"}
        )
        
        # Should return 403 Forbidden
        assert response.status_code == 403
        error_data = response.json()
        assert "forbidden" in error_data["error"]["code"].lower() or "author" in error_data["error"]["message"].lower()

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    @patch('app.services.solve_service.SolveService.set_solved_comment')
    def test_post_solve_non_question_thread(self, mock_set_solved, mock_get_current_user, mock_get_db_pool):
        """Test solve operation on non-question thread."""
        from app.util.errors import ValidationException
        
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        # Mock service to raise ValidationException with NOT_APPLICABLE
        mock_set_solved.side_effect = ValidationException(
            message="Solve operation is not applicable to non-question threads",
            details=[{"field": "thread.tags", "reason": "NOT_APPLICABLE"}]
        )
        
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": "cmt_01HX123456789ABCDEFGHJKMNP"}
        )
        
        # Should return 400 Validation Error
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        assert error_data["error"]["details"][0]["reason"] == "NOT_APPLICABLE"
        assert error_data["error"]["details"][0]["field"] == "thread.tags"

    @patch('app.core.db.get_db_pool')
    @patch('app.routers.solve.get_current_user')
    def test_post_solve_invalid_thread_id_format(self, mock_get_current_user, mock_get_db_pool):
        """Test solve operation with invalid thread ID format."""
        # Mock authentication
        mock_get_current_user.return_value = "usr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock database pool and connection  
        mock_conn = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value = MockAcquire(mock_conn)
        mock_get_db_pool.return_value = mock_pool
        
        response = self.client.post(
            "/api/v1/threads/invalid_id/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": "cmt_01HX123456789ABCDEFGHJKMNP"}
        )
        
        # Should return validation error or 404
        assert response.status_code in [400, 404, 422]

    def test_post_solve_invalid_comment_id_format(self):
        """Test solve operation with invalid comment ID format."""
        response = self.client.post(
            "/api/v1/threads/thr_01HX123456789ABCDEFGHJKMNP/solve",
            headers={"Authorization": "Bearer valid_token"},
            json={"commentId": "invalid_comment_id"}
        )
        
        # Should return validation error 
        assert response.status_code in [400, 422]