"""Reactions router."""

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import Response

from app.routers.auth import get_current_user, get_authorization_header
from app.core.db import get_db_connection
from app.schemas.reactions import ReactionRequestComment, ReactionRequestThread
from app.services.reactions_service import ReactionService
from app.util.errors import ValidationException, ConflictException

router = APIRouter(
    prefix="",
    tags=["reactions"]
)


@router.post("/comments/{comment_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def post_comment_reaction(
    comment_id: str,
    reaction_request: ReactionRequestComment,
    authorization: str = Depends(get_authorization_header),
    db = Depends(get_db_connection)
) -> Response:
    """React to a comment with 'up' reaction.
    
    Args:
        comment_id: ID of the comment to react to
        reaction_request: Reaction request data with 'kind' field
        authorization: Authorization header
        db: Database connection
        
    Returns:
        Empty response with 204 No Content status
        
    Raises:
        ValidationException: If comment ID format is invalid
        ConflictException: If user already reacted to this comment
        HTTPException: If authentication fails
    """
    # Get current user ID
    user_id = await get_current_user(authorization)
    
    # Create service instance
    async with db as conn:
        service = ReactionService(db=conn)
        
        # Process the reaction based on kind
        if reaction_request.kind == "up":
            await service.react_comment_up(
                user_id=user_id,
                comment_id=comment_id
            )
        else:
            # This shouldn't happen due to pydantic validation in ReactionRequestComment
            # but we include it for completeness
            raise ValidationException("Invalid reaction kind for comments")
    
    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/threads/{thread_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def post_thread_reaction(
    thread_id: str,
    reaction_request: ReactionRequestThread,
    authorization: str = Depends(get_authorization_header),
    db = Depends(get_db_connection)
) -> Response:
    """React to a thread with 'up' or 'save' reaction.
    
    Args:
        thread_id: ID of the thread to react to
        reaction_request: Reaction request data with 'kind' field
        authorization: Authorization header
        db: Database connection
        
    Returns:
        Empty response with 204 No Content status
        
    Raises:
        ValidationException: If thread ID format is invalid or kind is invalid
        ConflictException: If user already reacted to this thread
        HTTPException: If authentication fails
    """
    # Get current user ID
    user_id = await get_current_user(authorization)
    
    # Create service instance
    async with db as conn:
        service = ReactionService(db=conn)
        
        # Process the reaction based on kind
        if reaction_request.kind == "up":
            await service.react_thread_up(
                user_id=user_id,
                thread_id=thread_id
            )
        elif reaction_request.kind == "save":
            await service.react_thread_save(
                user_id=user_id,
                thread_id=thread_id
            )
        else:
            # This shouldn't happen due to pydantic validation in ReactionRequestThread
            # but we include it for completeness
            raise ValidationException("Invalid reaction kind for threads")
    
    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)