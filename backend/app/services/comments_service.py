"""Comment service layer for business logic."""

from typing import Any
import re
from datetime import datetime, timezone

from app.repositories.comments_repo import CommentRepository
from app.schemas.comments import CreateCommentRequest, CreatedResponse, Comment, AuthorAffiliation, PaginatedComments
from app.util.errors import ValidationException, NotFoundException


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
    
    async def list_comments(
        self,
        *,
        thread_id: str,
        current_user_id: str,
        cursor: str = None
    ) -> PaginatedComments:
        """List comments for a thread in ASC order.
        
        Args:
            thread_id: ID of the parent thread
            current_user_id: ID of the current user
            cursor: Pagination cursor
            
        Returns:
            PaginatedComments with list of comment DTOs
            
        Raises:
            ValidationException: If cursor is invalid
        """
        anchor_created_at = None
        anchor_id = None
        
        # Parse cursor if provided
        if cursor:
            try:
                from app.util.cursor import decode_cursor
                cursor_data = decode_cursor(cursor)
                
                # Extract anchor data from cursor
                if "createdAt" in cursor_data and "id" in cursor_data:
                    # Parse ISO8601 timestamp to datetime
                    created_at_str = cursor_data["createdAt"]
                    anchor_created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    anchor_id = cursor_data["id"]
            except Exception:
                raise ValidationException("Invalid cursor format")
        
        # Get comments from repository
        comment_data_list = await self._repo.list_comments_by_thread(
            thread_id=thread_id,
            anchor_created_at=anchor_created_at,
            anchor_id=anchor_id,
            limit=20
        )
        
        # Convert to Comment DTOs
        comment_dtos = []
        for comment_data in comment_data_list:
            comment_dto = self._to_comment_dto(comment_data)
            comment_dtos.append(comment_dto)
        
        # Generate next cursor if we have more results
        next_cursor = None
        if len(comment_dtos) == 20:  # Full page indicates more results may exist
            last_comment = comment_data_list[-1]
            # Create cursor for next page
            try:
                from app.util.cursor import encode_cursor
                cursor_obj = {
                    "v": 1,
                    "createdAt": last_comment["created_at"].isoformat().replace("+00:00", "Z"),
                    "id": last_comment["id"]
                }
                next_cursor = encode_cursor(cursor_obj)
            except Exception:
                # If cursor generation fails, set to None
                next_cursor = None
        
        return PaginatedComments(
            items=comment_dtos,
            nextCursor=next_cursor
        )
    
    async def delete_comment(
        self,
        *,
        user_id: str,
        comment_id: str
    ) -> None:
        """Delete a comment by soft deletion.
        
        Args:
            user_id: ID of the user requesting deletion
            comment_id: ID of the comment to delete
            
        Raises:
            NotFoundException: If comment not found or user is not the author
        """
        # Call repository to perform soft deletion
        # Repository handles ownership validation
        deleted = await self._repo.soft_delete_comment(
            comment_id=comment_id,
            author_id=user_id
        )
        
        # If deletion failed (not found or not authorized), raise 404
        # This treats both scenarios the same for security (don't leak existence)
        if not deleted:
            raise NotFoundException("Comment not found")
        
        # TODO: Add logic to clear thread solved state if this was the solved comment
        # This will be implemented when threads repository methods are available
    
    def _to_comment_dto(self, comment_data: dict) -> Comment:
        """Convert comment data to Comment DTO.
        
        Args:
            comment_data: Comment data from repository
            
        Returns:
            Comment DTO
        """
        # Format timestamp
        created_at = comment_data.get("created_at")
        if hasattr(created_at, "isoformat"):
            created_at_str = created_at.isoformat().replace("+00:00", "Z")
        else:
            created_at_str = str(created_at)
        
        # Handle author affiliation
        author_affiliation = None
        if comment_data.get("author_faculty") or comment_data.get("author_year"):
            author_affiliation = AuthorAffiliation(
                faculty=comment_data.get("author_faculty"),
                year=comment_data.get("author_year")
            )
        
        # TODO: Handle images in P3 phase
        has_image = False
        image_url = None
        
        return Comment(
            id=comment_data["id"],
            body=comment_data["body"],
            createdAt=created_at_str,
            upCount=comment_data.get("up_count", 0),
            hasImage=has_image,
            imageUrl=image_url,
            authorAffiliation=author_affiliation
        )