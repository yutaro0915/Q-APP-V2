"""Thread service layer for business logic."""

from typing import Any, Optional
import re

from app.repositories.threads_repo import ThreadRepository
from app.schemas.threads import CreateThreadRequest, ThreadCard, ThreadDetail, Tag, AuthorAffiliation, PaginatedThreadCards
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
    
    async def get_thread(
        self,
        *,
        thread_id: str,
        current_user_id: str
    ) -> Optional[ThreadDetail]:
        """Get a thread by ID.
        
        Args:
            thread_id: ID of the thread to retrieve
            current_user_id: ID of the current user
            
        Returns:
            ThreadDetail DTO if thread exists and not deleted, None otherwise
            
        Raises:
            ValidationException: If thread ID format is invalid
        """
        # Validate thread ID format
        if not self._is_valid_thread_id(thread_id):
            raise ValidationException("Invalid thread ID")
        
        # Create repository instance
        repo = ThreadRepository(self._db)
        
        # Get thread from repository
        thread_data = await repo.get_thread_by_id(thread_id=thread_id)
        
        # Return None if thread doesn't exist or is deleted
        if not thread_data:
            return None
        
        # TODO: Get tags from database in later phase
        # For now, use empty list
        tags = []
        
        # Convert to ThreadDetail DTO
        return self._to_thread_detail(thread_data, current_user_id, tags)
    
    async def list_threads_new(
        self,
        *,
        cursor: Optional[str] = None,
        current_user_id: str
    ) -> PaginatedThreadCards:
        """List threads in newest order.
        
        Args:
            cursor: Pagination cursor
            current_user_id: ID of the current user
            
        Returns:
            PaginatedThreadCards with list of threads
            
        Raises:
            ValidationException: If cursor is invalid
        """
        # Validate cursor if provided
        if cursor:
            try:
                from app.util.cursor import decode_cursor, validate_threads_cursor
                cursor_data = decode_cursor(cursor)
                anchor, errors = validate_threads_cursor(cursor_data)
                if errors:
                    raise ValidationException("Invalid cursor format")
            except ValidationException:
                raise
            except Exception:
                raise ValidationException("Invalid cursor")
        
        # Create repository instance
        repo = ThreadRepository(self._db)
        
        # Get threads from repository
        result = await repo.list_threads_new(cursor=cursor, limit=20)
        
        # Convert threads to ThreadCards
        thread_cards = []
        for thread_data in result["items"]:
            # TODO: Get tags from database in later phase
            tags = []
            thread_card = self._to_thread_card(thread_data, current_user_id, tags)
            thread_cards.append(thread_card)
        
        # Use nextCursor directly from repository
        next_cursor = result.get("nextCursor", None)
        
        return PaginatedThreadCards(
            items=thread_cards,
            nextCursor=next_cursor
        )
    
    async def delete_thread(
        self,
        *,
        thread_id: str,
        current_user_id: str
    ) -> None:
        """Delete a thread (soft delete).
        
        Args:
            thread_id: ID of the thread to delete
            current_user_id: ID of the current user
            
        Raises:
            ValidationException: If thread ID is invalid
            NotFoundException: If thread doesn't exist or already deleted
            ForbiddenException: If user is not the owner
        """
        # Validate thread ID format
        if not self._is_valid_thread_id(thread_id):
            raise ValidationException("Invalid thread ID")
        
        # Create repository instance
        repo = ThreadRepository(self._db)
        
        # Get thread to check ownership
        thread_data = await repo.get_thread_by_id(thread_id=thread_id)
        
        # Check if thread exists
        if not thread_data:
            from app.util.errors import NotFoundException
            raise NotFoundException("Thread not found")
        
        # Check if already deleted
        if thread_data.get("deleted_at") is not None:
            from app.util.errors import NotFoundException
            raise NotFoundException("Thread not found")
        
        # Check ownership
        if thread_data["author_id"] != current_user_id:
            from app.util.errors import ForbiddenException
            raise ForbiddenException("You can only delete your own threads")
        
        # Perform soft delete
        await repo.soft_delete_thread(thread_id=thread_id, user_id=current_user_id)
    
    def _is_valid_thread_id(self, thread_id: str) -> bool:
        """Validate thread ID format.
        
        Args:
            thread_id: Thread ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Thread ID must match format: thr_{26 char ULID}
        if not thread_id or not thread_id.startswith("thr_"):
            return False
        
        ulid_part = thread_id[4:]  # Remove "thr_" prefix
        
        # ULID must be exactly 26 characters
        if len(ulid_part) != 26:
            return False
        
        # ULID uses specific character set (Crockford's base32, no I, L, O, U)
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        return all(c in valid_chars for c in ulid_part)
    
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
                faculty=None,  # TODO: Get from profile
                year=None  # TODO: Get from profile
            )
        )
    
    def _to_thread_detail(self, thread_data: dict, current_user_id: str, tags: list[Tag]) -> ThreadDetail:
        """Convert thread data to ThreadDetail DTO.
        
        Args:
            thread_data: Thread data from repository
            current_user_id: ID of the current user
            tags: List of tags for the thread
            
        Returns:
            ThreadDetail DTO
        """
        # Determine if thread belongs to current user
        is_mine = thread_data.get("author_id") == current_user_id
        
        # Format timestamps
        created_at = thread_data.get("created_at")
        if hasattr(created_at, "isoformat"):
            created_at_str = created_at.isoformat().replace("+00:00", "Z")
        else:
            created_at_str = str(created_at)
        
        last_activity_at = thread_data.get("last_activity_at", created_at)
        if hasattr(last_activity_at, "isoformat"):
            last_activity_at_str = last_activity_at.isoformat().replace("+00:00", "Z")
        else:
            last_activity_at_str = str(last_activity_at)
        
        return ThreadDetail(
            id=thread_data["id"],
            title=thread_data["title"],
            body=thread_data.get("body", ""),
            tags=tags,
            upCount=thread_data.get("up_count", 0),
            saveCount=thread_data.get("save_count", 0),
            createdAt=created_at_str,
            lastActivityAt=last_activity_at_str,
            solvedCommentId=thread_data.get("solved_comment_id"),
            hasImage=False,  # TODO: Check attachments table in P3
            imageUrl=None,  # TODO: Get from attachments in P3
            authorAffiliation=AuthorAffiliation(
                faculty=None,  # TODO: Get from profile
                year=None  # TODO: Get from profile
            ),
            isMine=is_mine
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