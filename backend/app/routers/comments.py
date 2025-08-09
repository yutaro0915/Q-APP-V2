"""Comments router."""

from typing import Any

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse

from app.routers.auth import get_current_user
from app.core.db import get_db_connection
from app.services.comments_service import CommentService
from app.util.errors import NotFoundException

router = APIRouter(
    prefix="/comments",
    tags=["comments"]
)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    authorization: str = Header(...),
    db = Depends(get_db_connection)
) -> None:
    """Delete a comment by ID.
    
    Args:
        comment_id: ID of the comment to delete
        authorization: Authorization header
        db: Database connection
        
    Returns:
        204 No Content on success
        
    Raises:
        401: Authentication required
        404: Comment not found or not authorized to delete
    """
    # Get current user ID from token
    user_id = await get_current_user(authorization)
    
    async with db as conn:
        service = CommentService(db=conn)
        await service.delete_comment(
            user_id=user_id,
            comment_id=comment_id
        )
    
    # Return 204 No Content - FastAPI handles this automatically
    return None