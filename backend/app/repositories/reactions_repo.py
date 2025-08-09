"""Repository for reaction persistence (DDL: reactions table)."""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Literal

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

    # ---- P2-API-Repo-Reactions-UpsertUp implementation ----
    async def insert_up_if_absent(
        self,
        target_type: Literal['thread', 'comment'],
        target_id: str,
        user_id: str,
    ) -> bool:
        """Insert 'up' reaction if not already present.
        
        Args:
            target_type: Either 'thread' or 'comment'
            target_id: ID of the target being reacted to
            user_id: ID of user performing the reaction
            
        Returns:
            True if new reaction was inserted, False if duplicate
            
        Raises:
            ValueError: If target_type is not 'thread' or 'comment'
        """
        if target_type not in ('thread', 'comment'):
            raise ValueError(f"Invalid target_type: {target_type}. Must be 'thread' or 'comment'")
        
        # Generate new reaction ID
        reaction_id = self._generate_reaction_id()
        
        # Use a transaction to ensure atomicity between reaction insert and count update
        async with self._db.transaction():
            # Insert reaction with ON CONFLICT DO NOTHING
            insert_query = """
                INSERT INTO reactions (id, user_id, target_type, target_id, kind, created_at)
                VALUES ($1, $2, $3, $4, 'up', NOW())
                ON CONFLICT (user_id, target_type, target_id, kind) DO NOTHING
            """
            
            result = await self._db.execute(
                insert_query,
                reaction_id,
                user_id,
                target_type,
                target_id
            )
            
            # Check if row was actually inserted by examining result
            # PostgreSQL returns "INSERT 0 1" for successful insert, "INSERT 0 0" for conflict
            rows_affected = int(result.split()[-1]) if result else 0
            
            if rows_affected > 0:
                # Increment up_count in the appropriate table
                if target_type == 'thread':
                    update_query = """
                        UPDATE threads 
                        SET up_count = up_count + 1 
                        WHERE id = $1
                    """
                else:  # target_type == 'comment'
                    update_query = """
                        UPDATE comments 
                        SET up_count = up_count + 1 
                        WHERE id = $1
                    """
                
                await self._db.execute(update_query, target_id)
                return True
            else:
                # Reaction already exists (conflict occurred)
                return False

    # ---- P2-API-Repo-Reactions-UpsertSave implementation ----
    async def insert_save_if_absent(
        self,
        target_id: str,
        user_id: str,
    ) -> bool:
        """Insert 'save' reaction on thread if not already present.
        
        Args:
            target_id: Thread ID being saved (only threads support save reactions)
            user_id: ID of user performing the save reaction
            
        Returns:
            True if new reaction was inserted, False if duplicate
        """
        # Generate new reaction ID
        reaction_id = self._generate_reaction_id()
        
        # Use a transaction to ensure atomicity between reaction insert and count update
        async with self._db.transaction():
            # Insert save reaction (thread only) with ON CONFLICT DO NOTHING
            insert_query = """
                INSERT INTO reactions (id, user_id, target_type, target_id, kind, created_at)
                VALUES ($1, $2, 'thread', $3, 'save', NOW())
                ON CONFLICT (user_id, target_type, target_id, kind) DO NOTHING
            """
            
            result = await self._db.execute(
                insert_query,
                reaction_id,
                user_id,
                target_id
            )
            
            # Check if row was actually inserted by examining result
            # PostgreSQL returns "INSERT 0 1" for successful insert, "INSERT 0 0" for conflict
            rows_affected = int(result.split()[-1]) if result else 0
            
            if rows_affected > 0:
                # Increment save_count in threads table
                update_query = """
                    UPDATE threads 
                    SET save_count = save_count + 1 
                    WHERE id = $1
                """
                
                await self._db.execute(update_query, target_id)
                return True
            else:
                # Reaction already exists (conflict occurred)
                return False

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