"""Profile service for user profile management."""

from typing import Any

from app.schemas.profile import MyProfile, PublicProfile, UpdateProfileRequest


class ProfileService:
    """Service for user profile business logic."""

    def __init__(self, profile_repo: Any) -> None:
        """Initialize with profile repository."""
        self._profile_repo = profile_repo

    async def get_my_profile(self, user_id: str) -> MyProfile:
        """Get my profile with all fields visible.
        
        Args:
            user_id: The user ID
            
        Returns:
            MyProfile with all fields
        """
        profile_data = await self._profile_repo.get_profile_by_user_id(user_id)
        
        if profile_data is None:
            # Return default profile for new user
            return MyProfile(
                id=user_id,
                faculty=None,
                year=None,
                faculty_public=False,
                year_public=False,
                created_at=None
            )
        
        return MyProfile(
            id=profile_data["id"],
            faculty=profile_data.get("faculty"),
            year=profile_data.get("year"),
            faculty_public=profile_data.get("faculty_public", False),
            year_public=profile_data.get("year_public", False),
            created_at=profile_data.get("created_at")
        )

    async def update_my_profile(self, user_id: str, profile_data: UpdateProfileRequest) -> None:
        """Update my profile.
        
        Args:
            user_id: The user ID
            profile_data: Profile update data
        """
        # Validate the request data (Pydantic handles this automatically)
        # Additional validation can be done here if needed
        
        # Convert to dict, excluding None values to allow partial updates
        update_dict = {}
        if profile_data.faculty is not None:
            update_dict["faculty"] = profile_data.faculty
        if profile_data.year is not None:
            update_dict["year"] = profile_data.year
        if profile_data.faculty_public is not None:
            update_dict["faculty_public"] = profile_data.faculty_public
        if profile_data.year_public is not None:
            update_dict["year_public"] = profile_data.year_public
        
        # Allow updates where only public flags are set
        if profile_data.faculty_public is True and "faculty" not in update_dict:
            update_dict["faculty"] = None
        if profile_data.year_public is True and "year" not in update_dict:
            update_dict["year"] = None
            
        await self._profile_repo.upsert_profile(user_id, update_dict)

    async def get_public_profile(self, user_id: str) -> PublicProfile:
        """Get public profile with privacy filtering applied.
        
        Args:
            user_id: The user ID
            
        Returns:
            PublicProfile with private fields filtered
        """
        profile_data = await self._profile_repo.get_public_profile(user_id)
        
        return PublicProfile(
            id=profile_data["id"],
            faculty=profile_data.get("faculty"),
            year=profile_data.get("year"),
            created_at=profile_data.get("created_at")
        )