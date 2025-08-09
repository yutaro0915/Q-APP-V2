"""Solve service layer for business logic."""

from typing import Any, Optional, Dict

from app.repositories.threads_repo import ThreadRepository
from app.repositories.comments_repo import CommentRepository
from app.util.errors import ValidationException, NotFoundException, ForbiddenException


class SolveService:
    """Service layer for solve operations."""
    
    def __init__(self, db: Any) -> None:
        self._db = db
        self._threads_repo = ThreadRepository(db)
        self._comments_repo = CommentRepository(db)
    
    async def set_solved_comment(
        self,
        *,
        user_id: str,
        thread_id: str,
        comment_id: str
    ) -> None:
        """Set a comment as the solved answer for a question thread.
        
        Args:
            user_id: ID of the user requesting the solve (must be thread author)
            thread_id: ID of the thread to mark as solved
            comment_id: ID of the comment to mark as the solution
            
        Returns:
            None (204 No Content)
            
        Raises:
            NotFoundException: If thread or comment not found
            ForbiddenException: If user is not the thread author
            ValidationException: If thread is not a question type
        """
        # 1. Get thread information and validate ownership
        thread_data = await self._threads_repo.get_thread_by_id(thread_id=thread_id)
        
        if thread_data is None:
            raise NotFoundException("Thread not found")
        
        # Check if user is the thread author
        if thread_data["author_id"] != user_id:
            raise ForbiddenException("Only thread author can set solved comment")
        
        # 2. Validate thread type - for now, assume all threads are question type
        # In future phases, this would check thread tags or type field
        # For P2, we'll implement the basic validation structure
        if not self._is_question_thread(thread_data):
            details = [{
                "field": "thread.tags",
                "reason": "NOT_APPLICABLE"
            }]
            raise ValidationException(
                message="Solve operation is not applicable to non-question threads",
                details=details
            )
        
        # 3. Get and validate comment
        comment_data = await self._get_comment_by_id(comment_id=comment_id)
        
        if comment_data is None:
            raise NotFoundException("Comment not found")
        
        # Check if comment is deleted
        if comment_data.get("deleted_at") is not None:
            raise NotFoundException("Comment not found")
        
        # Validate that comment belongs to the same thread
        if comment_data["thread_id"] != thread_id:
            raise NotFoundException("Comment not found")
        
        # 4. Update thread's solved_comment_id
        await self._update_thread_solved_comment(
            thread_id=thread_id,
            comment_id=comment_id
        )
    
    def _is_question_thread(self, thread_data: Dict[str, Any]) -> bool:
        """Check if thread is a question type.
        
        For P2, we determine based on title pattern or content.
        In future phases, this would check thread tags or type field.
        """
        # Simple heuristic: if title contains question words, treat as question
        # This is a placeholder for future tag-based classification
        title = thread_data.get("title", "").lower()
        question_indicators = ["question", "how", "why", "what", "when", "where", "which", "?"]
        
        # Check if title contains question indicators
        if any(indicator in title for indicator in question_indicators):
            return True
        
        # For titles like "General discussion", "Discussion", etc., treat as non-question
        non_question_indicators = ["discussion", "general", "topic", "chat"]
        if any(indicator in title for indicator in non_question_indicators):
            return False
        
        # Default to question type for backward compatibility
        return True
    
    async def _get_comment_by_id(self, *, comment_id: str) -> Optional[Dict[str, Any]]:
        """Get comment by ID from database.
        
        Args:
            comment_id: The comment ID to fetch
            
        Returns:
            Comment data dictionary or None if not found
        """
        query = """
            SELECT id, thread_id, author_id, body, created_at, deleted_at
            FROM comments
            WHERE id = $1
        """
        
        result = await self._db.fetchrow(query, comment_id)
        return dict(result) if result else None
    
    async def _update_thread_solved_comment(
        self,
        *,
        thread_id: str,
        comment_id: str
    ) -> None:
        """Update thread's solved_comment_id field.
        
        Args:
            thread_id: ID of the thread to update
            comment_id: ID of the comment to set as solved
        """
        query = """
            UPDATE threads
            SET solved_comment_id = $1
            WHERE id = $2
        """
        
        await self._db.execute(query, comment_id, thread_id)