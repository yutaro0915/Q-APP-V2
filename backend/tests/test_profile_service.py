"""Tests for ProfileService."""

import pytest
from unittest.mock import AsyncMock
from pydantic import ValidationError

from app.services.profile_service import ProfileService
from app.schemas.profile import MyProfile, PublicProfile, UpdateProfileRequest


@pytest.fixture
def mock_profile_repo():
    """Create a mock ProfileRepository."""
    return AsyncMock()


@pytest.fixture
def service(mock_profile_repo):
    """Create a ProfileService instance with mock repository."""
    return ProfileService(mock_profile_repo)


class TestProfileService:
    """Test ProfileService methods."""

    async def test_get_my_profile_existing_user(self, service, mock_profile_repo):
        """Test getting my profile for existing user."""
        # Mock repository response
        mock_profile_data = {
            "id": "usr_01234567890123456789012345",
            "faculty": "工学部",
            "year": 3,
            "faculty_public": True,
            "year_public": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_profile_repo.get_profile_by_user_id.return_value = mock_profile_data
        
        # Execute
        result = await service.get_my_profile("usr_01234567890123456789012345")
        
        # Assert
        assert isinstance(result, MyProfile)
        assert result.id == "usr_01234567890123456789012345"
        assert result.faculty == "工学部"
        assert result.year == 3
        assert result.faculty_public == True
        assert result.year_public == True
        mock_profile_repo.get_profile_by_user_id.assert_called_once_with("usr_01234567890123456789012345")

    async def test_get_my_profile_new_user(self, service, mock_profile_repo):
        """Test getting my profile for new user (returns default)."""
        # Mock repository response for non-existent user
        mock_profile_repo.get_profile_by_user_id.return_value = None
        
        # Execute
        result = await service.get_my_profile("usr_99999999999999999999999999")
        
        # Assert - should return default profile
        assert isinstance(result, MyProfile)
        assert result.id == "usr_99999999999999999999999999"
        assert result.faculty is None
        assert result.year is None
        assert result.faculty_public == False
        assert result.year_public == False

    async def test_update_my_profile_full_update(self, service, mock_profile_repo):
        """Test updating profile with all fields."""
        user_id = "usr_01234567890123456789012345"
        update_data = UpdateProfileRequest(
            faculty="理学部",
            year=2,
            faculty_public=True,
            year_public=False
        )
        
        mock_profile_repo.upsert_profile = AsyncMock()
        
        # Execute
        await service.update_my_profile(user_id, update_data)
        
        # Assert
        mock_profile_repo.upsert_profile.assert_called_once()
        call_args = mock_profile_repo.upsert_profile.call_args[0]
        assert call_args[0] == user_id
        profile_data = call_args[1]
        assert profile_data["faculty"] == "理学部"
        assert profile_data["year"] == 2
        assert profile_data["faculty_public"] == True
        assert profile_data["year_public"] == False

    async def test_update_my_profile_partial_update(self, service, mock_profile_repo):
        """Test updating profile with only some fields."""
        user_id = "usr_01234567890123456789012345"
        update_data = UpdateProfileRequest(faculty_public=True)
        
        mock_profile_repo.upsert_profile = AsyncMock()
        
        # Execute
        await service.update_my_profile(user_id, update_data)
        
        # Assert
        mock_profile_repo.upsert_profile.assert_called_once()
        call_args = mock_profile_repo.upsert_profile.call_args[0]
        profile_data = call_args[1]
        assert profile_data.get("faculty_public") == True
        assert "faculty" not in profile_data or profile_data["faculty"] is None

    async def test_update_my_profile_validation_faculty_too_long(self, service, mock_profile_repo):
        """Test faculty validation - too long."""
        user_id = "usr_01234567890123456789012345"
        
        # Execute and assert validation error during DTO creation
        with pytest.raises(ValidationError):
            UpdateProfileRequest(faculty="a" * 51)  # Too long

    async def test_update_my_profile_validation_year_out_of_range(self, service, mock_profile_repo):
        """Test year validation - out of range."""
        user_id = "usr_01234567890123456789012345"
        
        # Execute and assert validation error during DTO creation
        with pytest.raises(ValidationError):
            UpdateProfileRequest(year=11)  # Out of range

    async def test_get_public_profile_all_public(self, service, mock_profile_repo):
        """Test getting public profile with all fields public."""
        # Mock repository response
        mock_profile_data = {
            "id": "usr_01234567890123456789012345",
            "faculty": "文学部",
            "year": 1,
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_profile_repo.get_public_profile.return_value = mock_profile_data
        
        # Execute
        result = await service.get_public_profile("usr_01234567890123456789012345")
        
        # Assert
        assert isinstance(result, PublicProfile)
        assert result.faculty == "文学部"
        assert result.year == 1
        mock_profile_repo.get_public_profile.assert_called_once_with("usr_01234567890123456789012345")

    async def test_get_public_profile_private_fields(self, service, mock_profile_repo):
        """Test getting public profile with private fields filtered."""
        # Mock repository response with None for private fields
        mock_profile_data = {
            "id": "usr_01234567890123456789012345",
            "faculty": None,  # Private
            "year": None,     # Private
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_profile_repo.get_public_profile.return_value = mock_profile_data
        
        # Execute
        result = await service.get_public_profile("usr_01234567890123456789012345")
        
        # Assert
        assert isinstance(result, PublicProfile)
        assert result.faculty is None
        assert result.year is None

    async def test_get_public_profile_non_existent_user(self, service, mock_profile_repo):
        """Test getting public profile for non-existent user."""
        # Mock repository response for non-existent user
        mock_profile_data = {
            "id": "usr_99999999999999999999999999",
            "faculty": None,
            "year": None,
            "created_at": None
        }
        mock_profile_repo.get_public_profile.return_value = mock_profile_data
        
        # Execute
        result = await service.get_public_profile("usr_99999999999999999999999999")
        
        # Assert
        assert isinstance(result, PublicProfile)
        assert result.faculty is None
        assert result.year is None