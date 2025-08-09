"""Tests for ProfileRouter."""
import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Set environment variable for testing
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"

from app.main import app
from app.schemas.profile import MyProfile, UpdateProfileRequest

client = TestClient(app)


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


class TestProfileRouter:
    """Test ProfileRouter endpoints."""

    def test_get_my_profile_success(self, mock_db_pool):
        """Test GET /auth/me/profile with valid auth."""
        mock_pool, mock_connection = mock_db_pool
        
        # Mock session validation (for get_current_user)
        mock_connection.fetchrow = AsyncMock(return_value={
            "user_id": "usr_01234567890123456789012345",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=1)
        })
        
        # Mock profile repository response
        def mock_fetchrow_side_effect(query, *args):
            # For session validation
            if "sessions" in query:
                return {
                    "user_id": "usr_01234567890123456789012345", 
                    "expires_at": datetime.now(timezone.utc) + timedelta(days=1)
                }
            # For profile data
            elif "users" in query:
                return {
                    "id": "usr_01234567890123456789012345",
                    "faculty": "工学部", 
                    "year": 3,
                    "faculty_public": True,
                    "year_public": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            return None
        
        mock_connection.fetchrow.side_effect = mock_fetchrow_side_effect
        
        with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
            response = client.get(
                "/api/v1/auth/me/profile",
                headers={"Authorization": "Bearer valid-token"}
            )
            
            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert data["userId"] == "usr_01234567890123456789012345"
            assert "id" not in data  # Should not contain id key
            assert data["faculty"] == "工学部"
            assert data["year"] == 3
            assert data["faculty_public"] == True
            assert data["year_public"] == True

    def test_get_my_profile_unauthorized(self):
        """Test GET /auth/me/profile without authorization."""
        response = client.get("/api/v1/auth/me/profile")
        
        # Should get 400 (validation error) because authorization header is required
        assert response.status_code == 400

    def test_patch_my_profile_success(self, mock_db_pool):
        """Test PATCH /auth/me/profile with valid data."""
        mock_pool, mock_connection = mock_db_pool
        
        update_data = {
            "faculty": "理学部",
            "year": 2,
            "faculty_public": True,
            "year_public": False
        }
        
        # Mock session validation (for get_current_user) 
        mock_connection.fetchrow = AsyncMock(return_value={
            "user_id": "usr_01234567890123456789012345",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=1)
        })
        
        # Mock database execute for upsert operation
        mock_connection.execute = AsyncMock()
        
        with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
            response = client.patch(
                "/api/v1/auth/me/profile",
                headers={"Authorization": "Bearer valid-token"},
                json=update_data
            )
            
            # Assert response
            assert response.status_code == 204
            assert response.content == b""
            
            # Verify database update was called 
            mock_connection.execute.assert_called_once()

    def test_patch_my_profile_unauthorized(self):
        """Test PATCH /auth/me/profile without authorization."""
        update_data = {"faculty": "理学部"}
        
        response = client.patch("/api/v1/auth/me/profile", json=update_data)
        
        # Should get 400 (validation error) because authorization header is required
        assert response.status_code == 400

    def test_patch_my_profile_validation_error(self):
        """Test PATCH /auth/me/profile with invalid data."""
        update_data = {
            "faculty": "a" * 51,  # Too long
            "year": 15  # Out of range
        }
        
        response = client.patch(
            "/api/v1/auth/me/profile",
            headers={"Authorization": "Bearer valid-token"},
            json=update_data
        )
        
        # Should return 400 for validation error  
        assert response.status_code == 400

    def test_patch_my_profile_partial_update(self, mock_db_pool):
        """Test PATCH /auth/me/profile with partial data."""
        mock_pool, mock_connection = mock_db_pool
        
        update_data = {"faculty_public": True}
        
        # Mock session validation (for get_current_user) 
        mock_connection.fetchrow = AsyncMock(return_value={
            "user_id": "usr_01234567890123456789012345",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=1)
        })
        
        # Mock database execute for upsert operation
        mock_connection.execute = AsyncMock()
        
        with patch("app.core.db.get_db_pool", AsyncMock(return_value=mock_pool)):
            response = client.patch(
                "/api/v1/auth/me/profile",
                headers={"Authorization": "Bearer valid-token"},
                json=update_data
            )
            
            # Assert response
            assert response.status_code == 204
            mock_connection.execute.assert_called_once()