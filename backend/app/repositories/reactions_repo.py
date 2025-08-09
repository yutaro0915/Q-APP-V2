"""Repository for reaction persistence (DDL: reactions table)."""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from app.util.idgen import generate_id


class ReactionRepository:
    """Repository for reaction persistence (DDL: reactions table).
    
    This repository defines the interface and basic helpers for reaction management.
    Implements UPSERT operations for handling duplicate reactions with 409 Conflict.
    """

    def __init__(self, db: Any) -> None:
        """Initialize repository with database connection."""
        self._db = db

    # ---- helpers ----
    def _generate_reaction_id(self) -> str:
        """Generate a new reaction ID in rcn_* format."""
        return generate_id("rcn")

    def _now_utc(self) -> str:
        """Get current UTC timestamp in ISO8601 format."""
        return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # ---- interface signatures ----
    async def upsert_thread_reaction(
        self,
        *,
        user_id: str,
        target_id: str,
        reaction_type: str,
    ) -> bool:
        """Upsert a reaction on a thread.
        
        Args:
            user_id: User ID who is reacting
            target_id: Thread ID being reacted to
            reaction_type: Type of reaction ('up' or 'save')
            
        Returns:
            True if new reaction was created, False if duplicate (409 Conflict should be handled at service layer)
        """
        raise NotImplementedError("Implemented in subsequent Issues")

    async def upsert_comment_reaction(
        self,
        *,
        user_id: str,
        target_id: str,
        reaction_type: str,
    ) -> bool:
        """Upsert a reaction on a comment.
        
        Args:
            user_id: User ID who is reacting
            target_id: Comment ID being reacted to  
            reaction_type: Type of reaction ('up' only for comments)
            
        Returns:
            True if new reaction was created, False if duplicate (409 Conflict should be handled at service layer)
        """
        raise NotImplementedError("Implemented in subsequent Issues")

    async def get_reaction_counts(
        self,
        *,
        target_type: str,
        target_id: str,
    ) -> Dict[str, int]:
        """Get reaction counts for a specific target.
        
        Args:
            target_type: 'thread' or 'comment'
            target_id: ID of the target
            
        Returns:
            Dict with reaction counts, e.g., {'up': 5, 'save': 2}
        """
        raise NotImplementedError("Implemented in subsequent Issues")

    async def get_user_reactions(
        self,
        *,
        user_id: str,
        target_ids: List[str],
    ) -> Dict[str, List[str]]:
        """Get user's reactions for multiple targets.
        
        Args:
            user_id: User ID to check reactions for
            target_ids: List of target IDs to check
            
        Returns:
            Dict mapping target_id to list of reaction types
        """
        raise NotImplementedError("Implemented in subsequent Issues")