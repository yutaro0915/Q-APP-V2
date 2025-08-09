"""Threads router."""

from typing import Dict, Any

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse

from app.routers.auth import get_current_user
from app.core.db import get_db_connection
from app.schemas.threads import CreateThreadRequest
from app.services.threads_service import ThreadService

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