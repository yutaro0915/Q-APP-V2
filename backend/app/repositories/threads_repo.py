from __future__ import annotations

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
        """Return thread row (dict) or None if not found/soft-deleted."""
        raise NotImplementedError

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

