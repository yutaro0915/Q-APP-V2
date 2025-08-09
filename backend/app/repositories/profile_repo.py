"""Profile repository for user profile management."""

from typing import Any, Dict, Optional


class ProfileRepository:
    """Repository for user profile persistence (users table)."""

    def __init__(self, db: Any) -> None:
        """Initialize with database connection."""
        self._db = db

    async def get_profile_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            Profile data dict or None if not found
        """
        query = """
            SELECT 
                id,
                faculty,
                year,
                faculty_public,
                year_public,
                created_at
            FROM users
            WHERE id = $1
        """
        
        result = await self._db.fetch_one(query, user_id)
        return dict(result) if result else None

    async def upsert_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Insert or update user profile.
        
        Args:
            user_id: The user ID
            profile_data: Profile data containing faculty, year, and public flags
        """
        query = """
            UPDATE users 
            SET 
                faculty = $2,
                year = $3,
                faculty_public = $4,
                year_public = $5
            WHERE id = $1
        """
        
        await self._db.execute(
            query,
            user_id,
            profile_data.get("faculty"),
            profile_data.get("year"),
            profile_data.get("faculty_public", False),
            profile_data.get("year_public", False)
        )

    async def get_public_profile(self, user_id: str) -> Dict[str, Any]:
        """Get public profile with privacy settings applied.
        
        Args:
            user_id: The user ID
            
        Returns:
            Public profile data with private fields set to None
        """
        query = """
            SELECT 
                id,
                faculty,
                year,
                faculty_public,
                year_public,
                created_at
            FROM users
            WHERE id = $1
        """
        
        result = await self._db.fetch_one(query, user_id)
        
        if not result:
            # Return default profile for non-existent user
            return {
                "id": user_id,
                "faculty": None,
                "year": None,
                "created_at": None
            }
        
        # Apply privacy settings
        profile = dict(result)
        return {
            "id": profile["id"],
            "faculty": profile["faculty"] if profile.get("faculty_public") else None,
            "year": profile["year"] if profile.get("year_public") else None,
            "created_at": profile["created_at"]
        }