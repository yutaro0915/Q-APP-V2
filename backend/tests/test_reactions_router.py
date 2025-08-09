"""Tests for ReactionRouter."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.routers.reactions import router
from app.routers.auth import get_current_user, get_authorization_header  
from app.core.db import get_db_connection
from app.services.reactions_service import ReactionService
from app.util.errors import ValidationException, ConflictException, BaseAPIException, api_exception_handler


class TestReactionCommentRouter:
    """Test suite for comment reaction router."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        # Add exception handler for custom API exceptions
        self.app.add_exception_handler(BaseAPIException, api_exception_handler)
        self.client = TestClient(self.app)
    
    def _mock_dependencies(self, mock_user_id: str = "usr_01H0000000000000000000000X"):
        """Helper to set up dependency overrides."""
        
        # Mock auth dependency to return user ID directly
        def mock_get_auth_header():
            return "Bearer valid_token"
        
        async def mock_get_current_user(authorization: str) -> str:
            return mock_user_id
        
        # Mock database connection
        async def mock_get_db_connection():
            yield AsyncMock()
        
        # Override dependencies correctly
        self.app.dependency_overrides[get_authorization_header] = mock_get_auth_header
        self.app.dependency_overrides[get_current_user] = lambda auth: mock_user_id
        self.app.dependency_overrides[get_db_connection] = mock_get_db_connection
    
    @patch('app.routers.reactions.get_current_user')
    @patch('app.routers.reactions.get_authorization_header')
    @patch('app.routers.reactions.get_db_connection')
    @patch('app.routers.reactions.ReactionService')
    def test_post_comment_reaction_up_success(self, mock_service_class, mock_get_db_connection, mock_get_auth_header, mock_get_current_user):
        """Test successful comment up reaction (204 No Content)."""
        
        # Mock authentication
        mock_get_auth_header.return_value = "Bearer valid_token"
        mock_get_current_user.return_value = "usr_01H0000000000000000000000X"
        
        # Mock database connection
        mock_db_conn = AsyncMock()
        mock_get_db_connection.return_value.__aenter__ = AsyncMock(return_value=mock_db_conn)
        mock_get_db_connection.return_value.__aexit__ = AsyncMock()
        
        # Mock service
        mock_service = AsyncMock()
        mock_service.react_comment_up = AsyncMock(return_value=None)
        mock_service_class.return_value = mock_service
        
        # Make request
        response = self.client.post(
            "/comments/cmt_01H0000000000000000000000X/reactions",
            headers={"Authorization": "Bearer valid_token"},
            json={"kind": "up"}
        )
        
        # Should return 204 No Content
        assert response.status_code == 204
        
        # Verify service was called with correct parameters
        mock_service.react_comment_up.assert_called_once_with(
            user_id="usr_01H0000000000000000000000X",
            comment_id="cmt_01H0000000000000000000000X"
        )
    
    @patch('app.routers.reactions.get_current_user')
    @patch('app.routers.reactions.get_authorization_header')
    @patch('app.routers.reactions.get_db_connection')
    @patch('app.routers.reactions.ReactionService')
    def test_post_comment_reaction_conflict(self, mock_service_class, mock_get_db_connection, mock_get_auth_header, mock_get_current_user):
        """Test comment reaction when already exists (409 Conflict)."""
        
        # Mock authentication
        mock_get_auth_header.return_value = "Bearer valid_token"
        mock_get_current_user.return_value = "usr_01H0000000000000000000000X"
        
        # Mock database connection
        mock_db_conn = AsyncMock()
        mock_get_db_connection.return_value.__aenter__ = AsyncMock(return_value=mock_db_conn)
        mock_get_db_connection.return_value.__aexit__ = AsyncMock()
        
        # Mock service to raise ConflictException
        mock_service = AsyncMock()
        mock_service.react_comment_up = AsyncMock(
            side_effect=ConflictException("User has already reacted to this comment")
        )
        mock_service_class.return_value = mock_service
        
        # Make request
        response = self.client.post(
            "/comments/cmt_01H0000000000000000000000X/reactions",
            headers={"Authorization": "Bearer valid_token"},
            json={"kind": "up"}
        )
        
        # Should return 409 Conflict
        assert response.status_code == 409
        response_data = response.json()
        assert response_data["error"]["code"] == "CONFLICT"
        assert "already reacted" in response_data["error"]["message"].lower()
    
    @patch('app.routers.reactions.get_current_user')
    @patch('app.routers.reactions.get_authorization_header')
    @patch('app.routers.reactions.get_db_connection')
    @patch('app.routers.reactions.ReactionService')
    def test_post_comment_reaction_validation_error(self, mock_service_class, mock_get_db_connection, mock_get_auth_header, mock_get_current_user):
        """Test comment reaction with invalid comment ID format."""
        
        # Mock authentication
        mock_get_auth_header.return_value = "Bearer valid_token"
        mock_get_current_user.return_value = "usr_01H0000000000000000000000X"
        
        # Mock database connection
        mock_db_conn = AsyncMock()
        mock_get_db_connection.return_value.__aenter__ = AsyncMock(return_value=mock_db_conn)
        mock_get_db_connection.return_value.__aexit__ = AsyncMock()
        
        # Mock service to raise ValidationException
        mock_service = AsyncMock()
        mock_service.react_comment_up = AsyncMock(
            side_effect=ValidationException("Invalid comment ID")
        )
        mock_service_class.return_value = mock_service
        
        # Make request with invalid comment ID
        response = self.client.post(
            "/comments/invalid_comment_id/reactions",
            headers={"Authorization": "Bearer valid_token"},
            json={"kind": "up"}
        )
        
        # Should return 400 Bad Request
        assert response.status_code == 400
        response_data = response.json()
        assert response_data["error"]["code"] == "VALIDATION_ERROR"
        assert "invalid comment id" in response_data["error"]["message"].lower()
    
    def test_post_comment_reaction_invalid_kind(self):
        """Test comment reaction with invalid kind (save not allowed)."""
        # Set up dependency overrides for auth
        self._mock_dependencies()
        
        # Make request with invalid kind
        response = self.client.post(
            "/comments/cmt_01H0000000000000000000000X/reactions",
            headers={"Authorization": "Bearer valid_token"},
            json={"kind": "save"}  # save not allowed for comments
        )
        
        # Should return 422 Unprocessable Entity (pydantic validation)
        assert response.status_code == 422
    
    def test_post_comment_reaction_unauthorized(self):
        """Test comment reaction without authentication."""
        # Don't set up auth dependency overrides - let it fail naturally
        
        # Make request without authorization header
        response = self.client.post(
            "/comments/cmt_01H0000000000000000000000X/reactions",
            json={"kind": "up"}
        )
        
        # Should return 401 since the Authorization header is missing
        # (FastAPI dependency injection will properly handle this)
        assert response.status_code == 401
    
    def test_post_comment_reaction_malformed_bearer(self):
        """Test comment reaction with malformed bearer token."""
        # Set up dependency override that simulates auth failure
        def mock_auth_fail():
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        self.app.dependency_overrides[get_current_user] = mock_auth_fail
        
        # Make request with malformed authorization
        response = self.client.post(
            "/comments/cmt_01H0000000000000000000000X/reactions",
            headers={"Authorization": "invalid_format"},
            json={"kind": "up"}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401