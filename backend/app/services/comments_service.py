"""Comment service layer for business logic."""

from typing import Any
import re
from datetime import datetime, timezone

from app.repositories.comments_repo import CommentRepository
from app.schemas.comments import CreateCommentRequest, CreatedResponse
from app.util.errors import ValidationException


class CommentService:
    """Service layer for comment operations."""
    
    def __init__(self, db: Any) -> None:
        self._db = db
        self._repo = CommentRepository(db)
    
    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters from text."""
        # Remove all control characters except tab, newline, carriage return
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    def _validate_and_clean_text(self, text: str, field_name: str, max_length: int = None) -> str:
        """Validate and clean text input."""
        # Remove control characters first
        cleaned = self._remove_control_characters(text)
        
        # Trim whitespace
        cleaned = cleaned.strip()
        
        # Check if empty after cleaning
        if not cleaned:
            raise ValidationException(f"{field_name} cannot be empty")
        
        # Check length if specified
        if max_length and len(cleaned) > max_length:
            raise ValidationException(f"{field_name} must be {max_length} characters or less")
        
        return cleaned
    
    async def create_comment(
        self,
        *,
        user_id: str,
        thread_id: str,
        dto: CreateCommentRequest
    ) -> CreatedResponse:
        """Create a new comment.
        
        Args:
            user_id: ID of the user creating the comment
            thread_id: ID of the parent thread
            dto: Comment creation request DTO
            
        Returns:
            CreatedResponse with the new comment ID and timestamp
            
        Raises:
            ValidationException: If validation fails
        """
        # Validate and clean body
        body = self._validate_and_clean_text(dto.body, "body", max_length=1000)
        
        # Create comment in repository - may raise exceptions
        try:
            comment_id = await self._repo.create_comment(
                author_id=user_id,
                thread_id=thread_id,
                body=body,
                image_key=dto.imageKey
            )
        except Exception as e:
            # Propagate repository errors
            raise e
        
        # Return CreatedResponse
        return CreatedResponse(
            id=comment_id,
            createdAt=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )