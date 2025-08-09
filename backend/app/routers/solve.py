"""Solve router for thread solve operations."""

from typing import Any

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import Response

from app.routers.auth import get_current_user
from app.core.db import get_db_connection
from app.schemas.comments import SolveRequest
from app.services.solve_service import SolveService

router = APIRouter(
    prefix="/threads",
    tags=["solve"]
)


@router.post("/{thread_id}/solve", status_code=status.HTTP_204_NO_CONTENT)
async def solve_thread(
    thread_id: str,
    solve_request: SolveRequest,
    authorization: str = Header(...),
    db = Depends(get_db_connection)
) -> None:
    """Set or clear solved comment on a thread.
    
    Args:
        thread_id: ID of the thread to solve/unsolve
        solve_request: Request with optional comment ID
        authorization: Authorization header (required)
        db: Database connection
        
    Returns:
        204 No Content on success
        
    Raises:
        UnauthorizedException: If not authenticated
        ForbiddenException: If not the thread owner
        NotFoundException: If thread or comment not found
        ValidationException: If thread is not a question type or validation fails
    """
    # Get current user ID (authentication required)
    user_id = await get_current_user(authorization)
    
    async with db as conn:
        service = SolveService(db=conn)
        
        if solve_request.commentId is not None:
            # Set solved comment
            await service.set_solved_comment(
                user_id=user_id,
                thread_id=thread_id,
                comment_id=solve_request.commentId
            )
        else:
            # Clear solved comment
            await service.clear_solved_comment(
                user_id=user_id,
                thread_id=thread_id
            )
    
    # Return 204 No Content - FastAPI handles this automatically
    return Response(status_code=status.HTTP_204_NO_CONTENT)