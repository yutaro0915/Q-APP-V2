from __future__ import annotations

import datetime as _dt
from typing import Any, Optional, Sequence, Dict, List

from app.util.idgen import generate_id


class CommentRepository:
    """Repository for comment persistence (DDL: comments table).

    This repository defines the interface and basic helpers for comment operations.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    # ---- helpers ----
    def _generate_comment_id(self) -> str:
        """Generate a new comment ID with cmt_ prefix."""
        return generate_id("cmt")

    def _now_utc(self) -> str:
        """Get current UTC timestamp as ISO8601 string."""
        return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # ---- interface signatures ----
    async def create_comment(
        self,
        *,
        author_id: str,
        thread_id: str,
        body: str,
        image_key: Optional[str] = None,
    ) -> str:
        """Create a new comment and return the comment ID.
        
        Args:
            author_id: ID of the comment author (usr_*)
            thread_id: ID of the parent thread (thr_*)
            body: Comment body text (1-1000 chars)
            image_key: Optional S3 image key
            
        Returns:
            The new comment ID (cmt_*)
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            # Generate new comment ID and timestamp
            comment_id = self._generate_comment_id()
            now_utc = self._now_utc()
            
            try:
                # Insert comment into database with RETURNING
                insert_query = """
                    INSERT INTO comments (
                        id, thread_id, author_id, body, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5::timestamptz)
                    RETURNING id, created_at
                """
                
                result = await self._db.fetchrow(
                    insert_query,
                    comment_id,     # $1
                    thread_id,      # $2
                    author_id,      # $3
                    body,          # $4
                    now_utc        # $5
                )
                
                # Update thread's last_activity_at
                update_query = """
                    UPDATE threads 
                    SET last_activity_at = $2::timestamptz
                    WHERE id = $1
                """
                
                await self._db.execute(
                    update_query,
                    thread_id,     # $1
                    now_utc        # $2
                )
                
                # Return the created comment ID
                return result["id"]
                
            except Exception as e:
                # Check if it's a unique constraint violation (ID collision)
                import asyncpg
                if isinstance(e, asyncpg.UniqueViolationError):
                    # Retry with a new ID
                    if attempt < max_retries - 1:
                        continue
                    else:
                        # Max retries reached, propagate the error
                        raise
                else:
                    # For other errors (like foreign key violations), propagate immediately
                    raise
        
        # Should not reach here, but just in case
        raise Exception("Failed to create comment after max retries")

    async def list_comments_by_thread(
        self,
        *,
        thread_id: str,
        anchor_created_at: Optional[_dt.datetime] = None,
        anchor_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List comments for a thread in ASC order (oldest first).
        
        Args:
            thread_id: ID of the parent thread
            anchor_created_at: Cursor anchor timestamp
            anchor_id: Cursor anchor comment ID
            limit: Maximum number of comments to return (default 20)
            
        Returns:
            List of comment records as dictionaries
        """
        # Implementation will be added in P2-API-Repo-Comments-ListAsc
        raise NotImplementedError("list_comments_by_thread will be implemented in P2-API-Repo-Comments-ListAsc")

    async def soft_delete_comment(
        self,
        *,
        comment_id: str,
        author_id: str,
    ) -> bool:
        """Soft delete a comment by setting deleted_at timestamp.
        
        Args:
            comment_id: ID of the comment to delete
            author_id: ID of the requesting user (must be comment author)
            
        Returns:
            True if comment was deleted, False if not found or not owned by author
        """
        # Implementation will be added in P2-API-Repo-Comments-SoftDelete
        raise NotImplementedError("soft_delete_comment will be implemented in P2-API-Repo-Comments-SoftDelete")

    async def get_comment_by_id(
        self,
        *,
        comment_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a comment by ID.
        
        Args:
            comment_id: The comment ID to fetch
            
        Returns:
            Comment record as dictionary, or None if not found
        """
        # This method is not specified in the YAML but may be needed
        raise NotImplementedError("get_comment_by_id implementation pending")