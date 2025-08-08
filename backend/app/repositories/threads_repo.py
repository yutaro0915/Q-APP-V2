from __future__ import annotations

import re
from typing import Any, Dict, Optional, Sequence

from app.services.cursor import encode, decode, CursorDecodeError
from app.util.idgen import generate_id


class ThreadRepository:
    """Repository for thread persistence (DDL: threads table).

    This repository defines only the interface and minimal helpers in P1 init.
    Actual SQL implementations are added in subsequent Issues.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    # ---- helpers ----
    def _generate_thread_id(self) -> str:
        return generate_id("thr")

    def _now_utc(self) -> str:
        # ISO8601 UTC string; later we may switch to timezone-aware datetime
        import datetime as _dt

        return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # ---- interface signatures ----
    async def create_thread(
        self,
        *,
        author_id: str,
        title: str,
        body: str,
        tags: Optional[Sequence[str]] = None,
        image_key: Optional[str] = None,
    ) -> str:
        """Create a new thread and return the new thread id."""
        raise NotImplementedError

    async def get_thread_by_id(self, *, thread_id: str) -> Optional[dict]:
        """Return thread row (dict) or None if not found/soft-deleted.
        
        Args:
            thread_id: Thread ID in format thr_ULID
            
        Returns:
            Thread data as dict if found and not deleted, None otherwise
        """
        # Validate thread ID format
        if not self._is_valid_thread_id(thread_id):
            return None
        
        # Query for thread excluding soft-deleted ones
        query = """
            SELECT * FROM threads
            WHERE id = $1 AND deleted_at IS NULL
        """
        
        result = await self._db.fetchrow(query, thread_id)
        
        # Convert to dict if found, otherwise return None
        return dict(result) if result else None
    
    def _is_valid_thread_id(self, thread_id: str) -> bool:
        """Validate thread ID format.
        
        Thread IDs must match: thr_[26 ULID chars]
        ULID charset: 0-9, A-H, J, K, M, N, P-T, V-Z
        """
        if not thread_id:
            return False
        
        # Check prefix and length
        if not thread_id.startswith("thr_"):
            return False
        
        if len(thread_id) != 30:  # thr_ (4) + ULID (26)
            return False
        
        # Validate ULID characters
        ulid_part = thread_id[4:]
        ulid_pattern = re.compile(r'^[0-9A-HJKMNP-TV-Z]{26}$')
        
        return bool(ulid_pattern.match(ulid_part))

    async def list_threads_new(
        self,
        *,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Return items and nextCursor for timeline 'new'.
        
        Args:
            cursor: Optional cursor string for pagination
            limit: Number of items to return (default 20, max 200)
            
        Returns:
            Dict with 'items' list and optional 'nextCursor'
        """
        # Enforce maximum limit
        if limit > 200:
            limit = 200
        
        # Parse cursor if provided
        anchor_created_at = None
        anchor_id = None
        
        if cursor:
            try:
                cursor_obj = decode(cursor)
                # Validate cursor format
                if cursor_obj.get("v") != 1:
                    # Invalid cursor, just ignore it
                    pass
                else:
                    anchor_created_at = cursor_obj.get("createdAt")
                    anchor_id = cursor_obj.get("id")
            except CursorDecodeError:
                # Invalid cursor, proceed without it
                pass
        
        # Build query
        if anchor_created_at and anchor_id:
            # With cursor: get threads before the anchor
            query = """
                SELECT * FROM threads
                WHERE deleted_at IS NULL
                  AND (created_at, id) < ($1, $2)
                ORDER BY created_at DESC, id DESC
                LIMIT $3
            """
            # Fetch limit+1 to check if there are more
            rows = await self._db.fetch(query, anchor_created_at, anchor_id, limit + 1)
        else:
            # Without cursor: get latest threads
            query = """
                SELECT * FROM threads
                WHERE deleted_at IS NULL
                ORDER BY created_at DESC, id DESC
                LIMIT $1
            """
            # Fetch limit+1 to check if there are more
            rows = await self._db.fetch(query, limit + 1)
        
        # Convert rows to list of dicts
        items = [dict(row) for row in rows]
        
        # Check if there are more pages
        has_more = len(items) > limit
        if has_more:
            # Remove the extra item
            items = items[:limit]
        
        # Generate next cursor if there are more pages
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            cursor_obj = {
                "v": 1,
                "createdAt": last_item["created_at"].isoformat().replace("+00:00", "Z"),
                "id": last_item["id"]
            }
            next_cursor = encode(cursor_obj)
        
        return {
            "items": items,
            "nextCursor": next_cursor
        }

    async def soft_delete_thread(self, *, thread_id: str, author_id: str) -> bool:
        """Soft delete the thread (set deleted_at).
        
        Args:
            thread_id: Thread ID to delete
            author_id: User ID of the requester (must be the owner)
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        # Validate thread ID format
        if not self._is_valid_thread_id(thread_id):
            return False
        
        # Get current timestamp for deleted_at
        now = self._now_utc()
        
        # Update the thread only if:
        # 1. The thread exists
        # 2. The requester is the owner
        # 3. The thread is not already deleted
        query = """
            UPDATE threads
            SET deleted_at = $1
            WHERE id = $2
              AND author_id = $3
              AND deleted_at IS NULL
            RETURNING id
        """
        
        result = await self._db.fetchrow(query, now, thread_id, author_id)
        
        # If a row was updated, result will contain the id
        return result is not None

