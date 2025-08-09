"""Tests for ProfileRepository."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.repositories.profile_repo import ProfileRepository


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = AsyncMock()
    return db


@pytest.fixture
def repo(mock_db):
    """Create a ProfileRepository instance with mock database."""
    return ProfileRepository(mock_db)


class TestProfileRepository:
    """Test ProfileRepository methods."""

    async def test_get_profile_by_user_id_existing(self, repo, mock_db):
        """Test getting an existing user profile."""
        # Mock data
        mock_profile = {
            "id": "usr_01234567890123456789012345",
            "faculty": "工学部",
            "year": 3,
            "faculty_public": True,
            "year_public": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_db.fetch_one = AsyncMock(return_value=mock_profile)
        
        # Execute
        result = await repo.get_profile_by_user_id("usr_01234567890123456789012345")
        
        # Assert
        assert result == mock_profile
        mock_db.fetch_one.assert_called_once()
        
    async def test_get_profile_by_user_id_not_found(self, repo, mock_db):
        """Test getting profile for non-existent user."""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        result = await repo.get_profile_by_user_id("usr_99999999999999999999999999")
        
        assert result is None
        mock_db.fetch_one.assert_called_once()

    async def test_upsert_profile_insert(self, repo, mock_db):
        """Test inserting a new profile."""
        user_id = "usr_01234567890123456789012345"
        profile_data = {
            "faculty": "理学部",
            "year": 2,
            "faculty_public": True,
            "year_public": False
        }
        
        mock_db.execute = AsyncMock()
        
        # Execute
        await repo.upsert_profile(user_id, profile_data)
        
        # Assert
        mock_db.execute.assert_called_once()
        
    async def test_upsert_profile_update(self, repo, mock_db):
        """Test updating an existing profile."""
        user_id = "usr_01234567890123456789012345"
        profile_data = {
            "faculty": "医学部",
            "year": 4,
            "faculty_public": False,
            "year_public": True
        }
        
        mock_db.execute = AsyncMock()
        
        # Execute
        await repo.upsert_profile(user_id, profile_data)
        
        # Assert
        mock_db.execute.assert_called_once()
        
    async def test_get_public_profile_all_public(self, repo, mock_db):
        """Test getting public profile with all fields public."""
        mock_profile = {
            "id": "usr_01234567890123456789012345",
            "faculty": "文学部",
            "year": 1,
            "faculty_public": True,
            "year_public": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_db.fetch_one = AsyncMock(return_value=mock_profile)
        
        result = await repo.get_public_profile("usr_01234567890123456789012345")
        
        assert result["faculty"] == "文学部"
        assert result["year"] == 1
        
    async def test_get_public_profile_partially_public(self, repo, mock_db):
        """Test getting public profile with some fields private."""
        mock_profile = {
            "id": "usr_01234567890123456789012345",
            "faculty": "法学部",
            "year": 3,
            "faculty_public": True,
            "year_public": False,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_db.fetch_one = AsyncMock(return_value=mock_profile)
        
        result = await repo.get_public_profile("usr_01234567890123456789012345")
        
        assert result["faculty"] == "法学部"
        assert result["year"] is None  # Private field should be None
        
    async def test_get_public_profile_all_private(self, repo, mock_db):
        """Test getting public profile with all fields private."""
        mock_profile = {
            "id": "usr_01234567890123456789012345",
            "faculty": "経済学部",
            "year": 2,
            "faculty_public": False,
            "year_public": False,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_db.fetch_one = AsyncMock(return_value=mock_profile)
        
        result = await repo.get_public_profile("usr_01234567890123456789012345")
        
        assert result["faculty"] is None
        assert result["year"] is None
        
    async def test_get_public_profile_not_found(self, repo, mock_db):
        """Test getting public profile for non-existent user."""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        result = await repo.get_public_profile("usr_99999999999999999999999999")
        
        # Should return default profile
        assert result is not None
        assert result["faculty"] is None
        assert result["year"] is None