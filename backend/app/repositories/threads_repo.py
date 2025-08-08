from __future__ import annotations

import re
from typing import Any, Optional, Sequence

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
        cursor: Optional[dict] = None,
        limit: int = 20,
    ) -> dict:
        """Return items and nextCursor for timeline 'new'."""
        raise NotImplementedError

    async def soft_delete_thread(self, *, thread_id: str, author_id: str) -> None:
        """Soft delete the thread (set deleted_at)."""
        raise NotImplementedError

