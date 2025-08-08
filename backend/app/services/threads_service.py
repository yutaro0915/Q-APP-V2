"""Thread service layer for business logic."""

from typing import Any, Optional
import re

from app.repositories.threads_repo import ThreadRepository
from app.schemas.threads import CreateThreadRequest, ThreadCard, Tag, AuthorAffiliation
from app.util.errors import ValidationException


class ThreadService:
    """Service layer for thread operations."""
    
    def __init__(self, db: Any) -> None:
        self._db = db
    
    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters from text."""
        # Remove all control characters except tab, newline, carriage return
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    def _validate_and_clean_text(self, text: str, field_name: str, allow_empty: bool = False) -> str:
        """Validate and clean text input."""
        # Remove control characters first
        cleaned = self._remove_control_characters(text)
        
        # Trim whitespace
        cleaned = cleaned.strip()
        
        # Check if empty after cleaning
        if not cleaned and not allow_empty:
            raise ValidationException(f"{field_name} cannot be empty")
        
        return cleaned
    
    async def create_thread(
        self,
        *,
        user_id: str,
        thread_create: CreateThreadRequest
    ) -> ThreadCard:
        """Create a new thread.
        
        Args:
            user_id: ID of the user creating the thread
            thread_create: Thread creation request DTO
            
        Returns:
            ThreadCard DTO of the created thread
            
        Raises:
            ValidationException: If validation fails
        """
        # Validate and clean title
        title = self._validate_and_clean_text(thread_create.title, "title", allow_empty=False)
        
        # Validate and clean body (can be empty)
        body = self._validate_and_clean_text(thread_create.body, "body", allow_empty=True)
        
        # Create repository instance
        repo = ThreadRepository(self._db)
        
        # Create thread in repository - may raise exceptions
        try:
            thread_id = await repo.create_thread(
                author_id=user_id,
                title=title,
                body=body,
                tags=thread_create.tags,
                image_key=thread_create.imageKey
            )
        except Exception as e:
            # Propagate repository errors
            raise e
        
        # Get the created thread to return as ThreadCard
        thread_data = await repo.get_thread_by_id(thread_id=thread_id)
        
        if not thread_data:
            # This shouldn't happen, but handle it gracefully
            raise Exception("Failed to retrieve created thread")
        
        # Convert to ThreadCard DTO
        return self._to_thread_card(thread_data, user_id, thread_create.tags)
    
    def _to_thread_card(self, thread_data: dict, current_user_id: str, tags: list[Tag]) -> ThreadCard:
        """Convert thread data to ThreadCard DTO.
        
        Args:
            thread_data: Thread data from repository
            current_user_id: ID of the current user
            tags: List of tags for the thread
            
        Returns:
            ThreadCard DTO
        """
        # Create excerpt from body
        excerpt = self._create_excerpt(thread_data.get("body", ""))
        
        # Determine if thread is solved
        is_solved = thread_data.get("solved_comment_id") is not None
        
        # Determine if thread belongs to current user
        is_mine = thread_data.get("author_id") == current_user_id
        
        # TODO: Get actual comment count from comments table in later phase
        comment_count = 0
        
        # Format timestamp
        created_at = thread_data.get("created_at")
        if hasattr(created_at, "isoformat"):
            created_at_str = created_at.isoformat().replace("+00:00", "Z")
        else:
            created_at_str = str(created_at)
        
        return ThreadCard(
            id=thread_data["id"],
            title=thread_data["title"],
            excerpt=excerpt,
            tags=tags,
            heat=int(thread_data.get("heat", 0)),
            replies=comment_count,
            saves=thread_data.get("save_count", 0),
            createdAt=created_at_str,
            lastReplyAt=None,  # TODO: Get from comments table
            hasImage=False,  # TODO: Check attachments table in P3
            imageThumbUrl=None,
            solved=is_solved,
            authorAffiliation=AuthorAffiliation(
                id=thread_data["author_id"],
                displayName="User",  # TODO: Get from users table
                isPublic=True,  # TODO: Get from profile
                faculty=None,
                year=None
            )
        )
    
    def _create_excerpt(self, body: str, max_length: int = 100) -> str:
        """Create an excerpt from body text.
        
        Args:
            body: Full body text
            max_length: Maximum excerpt length
            
        Returns:
            Excerpt string
        """
        if not body:
            return ""
        
        # Normalize whitespace
        excerpt = " ".join(body.split())
        
        # Truncate if needed
        if len(excerpt) <= max_length:
            return excerpt
        
        # Truncate at word boundary if possible
        truncated = excerpt[:max_length]
        last_space = truncated.rfind(" ")
        
        if last_space > max_length * 0.8:  # If we can keep at least 80% of the text
            return truncated[:last_space] + "..."
        
        return truncated + "..."