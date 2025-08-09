"""Tests for ReactionRepository."""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.repositories.reactions_repo import ReactionRepository


class TestReactionRepository:
    """Test suite for ReactionRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = AsyncMock()
        self.repo = ReactionRepository(self.mock_db)
    
    def test_reaction_repository_instantiation(self):
        """Test that ReactionRepository can be instantiated."""
        repo = ReactionRepository(self.mock_db)
        assert repo is not None
        assert hasattr(repo, '_db')
    
    def test_reaction_repository_has_required_methods(self):
        """Test that ReactionRepository has all required method signatures."""
        # Check that all required methods exist
        assert hasattr(self.repo, 'upsert_thread_reaction')
        assert callable(getattr(self.repo, 'upsert_thread_reaction'))
        
        assert hasattr(self.repo, 'upsert_comment_reaction')
        assert callable(getattr(self.repo, 'upsert_comment_reaction'))
        
        assert hasattr(self.repo, 'get_reaction_counts')
        assert callable(getattr(self.repo, 'get_reaction_counts'))
        
        assert hasattr(self.repo, 'get_user_reactions')
        assert callable(getattr(self.repo, 'get_user_reactions'))
    
    def test_reaction_id_generation(self):
        """Test that reaction ID is generated in correct format."""
        reaction_id = self.repo._generate_reaction_id()
        assert reaction_id.startswith('rcn_')
        assert len(reaction_id) == 30  # 'rcn_' + 26 character ULID
        
        # Generate multiple IDs to ensure uniqueness
        ids = {self.repo._generate_reaction_id() for _ in range(10)}
        assert len(ids) == 10  # All IDs should be unique
    
    def test_now_utc_helper(self):
        """Test that _now_utc returns correct timestamp format."""
        timestamp = self.repo._now_utc()
        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        # Should be in format like '2023-01-01T12:00:00Z'
        assert len(timestamp) == 20
    
    @pytest.mark.asyncio
    async def test_upsert_thread_reaction_signature(self):
        """Test upsert_thread_reaction method signature (currently just raises NotImplementedError)."""
        with pytest.raises(NotImplementedError):
            await self.repo.upsert_thread_reaction(
                user_id="usr_01H0000000000000000000000", 
                target_id="thr_01H0000000000000000000000", 
                reaction_type="up"
            )
    
    @pytest.mark.asyncio
    async def test_upsert_comment_reaction_signature(self):
        """Test upsert_comment_reaction method signature (currently just raises NotImplementedError)."""
        with pytest.raises(NotImplementedError):
            await self.repo.upsert_comment_reaction(
                user_id="usr_01H0000000000000000000000", 
                target_id="cmt_01H0000000000000000000000", 
                reaction_type="up"
            )
    
    @pytest.mark.asyncio
    async def test_get_reaction_counts_signature(self):
        """Test get_reaction_counts method signature (currently just raises NotImplementedError)."""
        with pytest.raises(NotImplementedError):
            await self.repo.get_reaction_counts(
                target_type="thread",
                target_id="thr_01H0000000000000000000000"
            )
    
    @pytest.mark.asyncio
    async def test_get_user_reactions_signature(self):
        """Test get_user_reactions method signature (currently just raises NotImplementedError)."""
        with pytest.raises(NotImplementedError):
            await self.repo.get_user_reactions(
                user_id="usr_01H0000000000000000000000",
                target_ids=["thr_01H0000000000000000000000"]
            )