"""Threads router."""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse

from app.routers.auth import get_current_user
from app.core.db import get_db_connection
from app.schemas.threads import CreateThreadRequest, PaginatedThreadCards, ThreadDetail
from app.services.threads_service import ThreadService
from app.util.errors import ValidationException

router = APIRouter(
    prefix="/threads",
    tags=["threads"]
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_thread(
    thread_create: CreateThreadRequest,
    authorization: str = Header(...),
    db = Depends(get_db_connection)
) -> Dict[str, Any]:
    """Create a new thread.
    
    Args:
        thread_create: Thread creation request
        authorization: Authorization header
        db: Database connection
        
    Returns:
        Created response with thread ID and timestamp
    """
    # Get current user ID
    user_id = await get_current_user(authorization)
    
    async with db as conn:
        service = ThreadService(db=conn)
        thread_card = await service.create_thread(
            user_id=user_id,
            thread_create=thread_create
        )
        
        # Return only id and createdAt for 201 response
        return {
            "id": thread_card.id,
            "createdAt": thread_card.createdAt
        }


@router.get("", response_model=PaginatedThreadCards)
async def list_threads(
    request: Request,
    sort: str = Query("new", description="Sort order: 'new' or 'hot'"),
    type: Optional[str] = Query(None, description="Thread type filter"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    db = Depends(get_db_connection)
) -> PaginatedThreadCards:
    """List threads with pagination.
    
    Args:
        request: FastAPI request object
        sort: Sort order ('new' for phase 1, 'hot' not implemented)
        type: Thread type filter (not implemented in phase 1)
        cursor: Pagination cursor
        db: Database connection
        
    Returns:
        Paginated list of thread cards
    """
    # Phase 1: Only support 'new' sort
    if sort != "new":
        raise ValidationException("Only 'new' sort is supported in Phase 1")
    
    # Try to get current user from authorization header
    current_user_id = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            current_user_id = await get_current_user(auth_header)
        except Exception:
            # Authentication is optional for listing threads
            pass
    
    async with db as conn:
        service = ThreadService(db=conn)
        return await service.list_threads_new(
            current_user_id=current_user_id,
            cursor=cursor
        )


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread_detail(
    thread_id: str,
    request: Request,
    db = Depends(get_db_connection)
) -> ThreadDetail:
    """Get thread detail by ID.
    
    Args:
        thread_id: Thread ID
        request: FastAPI request object
        db: Database connection
        
    Returns:
        Thread detail
        
    Raises:
        NotFoundException: If thread doesn't exist or is deleted
        ValidationException: If thread ID format is invalid
    """
    # Try to get current user from authorization header
    current_user_id = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            current_user_id = await get_current_user(auth_header)
        except Exception:
            # Authentication is optional for getting thread detail
            pass
    
    async with db as conn:
        service = ThreadService(db=conn)
        return await service.get_thread(
            thread_id=thread_id,
            current_user_id=current_user_id
        )


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    authorization: str = Header(...),
    db = Depends(get_db_connection)
) -> None:
    """Delete a thread (soft delete).
    
    Args:
        thread_id: Thread ID to delete
        authorization: Authorization header (required)
        db: Database connection
        
    Returns:
        None (204 No Content)
        
    Raises:
        UnauthorizedException: If not authenticated
        ForbiddenException: If not the thread owner
        NotFoundException: If thread doesn't exist
        ValidationException: If thread ID format is invalid
    """
    # Get current user ID (authentication required)
    current_user_id = await get_current_user(authorization)
    
    async with db as conn:
        service = ThreadService(db=conn)
        await service.delete_thread(
            thread_id=thread_id,
            current_user_id=current_user_id
        )