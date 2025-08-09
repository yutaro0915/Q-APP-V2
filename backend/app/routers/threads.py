"""Threads router."""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse

from app.routers.auth import get_current_user
from app.core.db import get_db_connection
from app.schemas.threads import CreateThreadRequest, PaginatedThreadCards
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