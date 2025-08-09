"""Profile router."""

from fastapi import APIRouter, Depends, Header, status

from app.routers.auth import get_current_user
from app.core.db import get_db_connection
from app.schemas.profile import MyProfile, UpdateProfileRequest
from app.services.profile_service import ProfileService
from app.repositories.profile_repo import ProfileRepository

router = APIRouter(
    prefix="/auth/me",
    tags=["profile"]
)


@router.get("/profile", response_model=MyProfile)
async def get_my_profile(
    authorization: str = Header(...),
    db = Depends(get_db_connection)
) -> MyProfile:
    """Get my profile with all fields visible.
    
    Args:
        authorization: Authorization header (required)
        db: Database connection
        
    Returns:
        MyProfile with all fields
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get current user ID (authentication required)
    user_id = await get_current_user(authorization)
    
    async with db as conn:
        profile_repo = ProfileRepository(conn)
        service = ProfileService(profile_repo)
        return await service.get_my_profile(user_id)


@router.patch("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def update_my_profile(
    profile_data: UpdateProfileRequest,
    authorization: str = Header(...),
    db = Depends(get_db_connection)
) -> None:
    """Update my profile.
    
    Args:
        profile_data: Profile update data
        authorization: Authorization header (required) 
        db: Database connection
        
    Returns:
        None (204 No Content)
        
    Raises:
        HTTPException: If authentication fails
        ValidationError: If profile data is invalid
    """
    # Get current user ID (authentication required)
    user_id = await get_current_user(authorization)
    
    async with db as conn:
        profile_repo = ProfileRepository(conn)
        service = ProfileService(profile_repo)
        await service.update_my_profile(user_id, profile_data)