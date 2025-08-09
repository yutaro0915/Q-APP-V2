"""Service layer for reaction operations."""

from typing import Any, Optional
from app.repositories.reactions_repo import ReactionRepository
from app.util.errors import ValidationException, ConflictException


class ReactionService:
    """Service layer for reaction operations."""
    
    def __init__(self, db: Any) -> None:
        """Initialize service with database connection."""
        self._db = db
    
    async def react_comment_up(
        self,
        *,
        user_id: str,
        comment_id: str,
    ) -> None:
        """React with 'up' on a comment.
        
        Args:
            user_id: ID of the user performing the reaction
            comment_id: ID of the comment being reacted to
            
        Returns:
            None (success results in 204 No Content)
            
        Raises:
            ValidationException: If comment ID format is invalid
            ConflictException: If user already reacted to this comment
        """
        # Validate comment ID format
        if not self._is_valid_comment_id(comment_id):
            raise ValidationException("Invalid comment ID")
        
        # Create repository instance
        repo = ReactionRepository(self._db)
        
        # Try to insert the reaction
        was_inserted = await repo.insert_up_if_absent(
            target_type="comment",
            target_id=comment_id,
            user_id=user_id
        )
        
        # If reaction already exists, raise conflict error
        if not was_inserted:
            raise ConflictException("User has already reacted to this comment")
        
        # Success - return None for 204 No Content
        return None
    
    async def react_thread_up(
        self,
        *,
        user_id: str,
        thread_id: str,
    ) -> None:
        """React with 'up' on a thread.
        
        Args:
            user_id: ID of the user performing the reaction
            thread_id: ID of the thread being reacted to
            
        Returns:
            None (success results in 204 No Content)
            
        Raises:
            ValidationException: If thread ID format is invalid
            ConflictException: If user already reacted to this thread
        """
        # Validate thread ID format
        if not self._is_valid_thread_id(thread_id):
            raise ValidationException("Invalid thread ID")
        
        # Create repository instance
        repo = ReactionRepository(self._db)
        
        # Try to insert the reaction
        was_inserted = await repo.insert_up_if_absent(
            target_type="thread",
            target_id=thread_id,
            user_id=user_id
        )
        
        # If reaction already exists, raise conflict error
        if not was_inserted:
            raise ConflictException("User has already reacted to this thread")
        
        # Success - return None for 204 No Content
        return None
    
    def _is_valid_comment_id(self, comment_id: str) -> bool:
        """Validate comment ID format.
        
        Args:
            comment_id: Comment ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Comment ID must match format: cmt_{26 char ULID}
        if not comment_id or not comment_id.startswith("cmt_"):
            return False
        
        ulid_part = comment_id[4:]  # Remove "cmt_" prefix
        
        # ULID must be exactly 26 characters
        if len(ulid_part) != 26:
            return False
        
        # ULID uses specific character set (Crockford's base32, no I, L, O, U)
        valid_chars = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
        return all(c in valid_chars for c in ulid_part)
    
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