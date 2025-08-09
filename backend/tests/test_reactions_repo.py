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

    # Tests for P2-API-Repo-Reactions-UpsertUp functionality
    @pytest.mark.asyncio
    async def test_insert_up_if_absent_thread_new_reaction(self):
        """Test insert_up_if_absent creates new thread reaction successfully."""
        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.mock_db.transaction = Mock(return_value=mock_transaction)
        
        # Mock database responses
        self.mock_db.execute = AsyncMock(return_value="INSERT 0 1")  # 1 row affected
        
        result = await self.repo.insert_up_if_absent("thread", "thr_01H0000000000000000000000", "usr_01H0000000000000000000000")
        
        assert result is True
        # Verify transaction was called
        self.mock_db.transaction.assert_called_once()
        # Verify execute was called twice (INSERT + UPDATE)
        assert self.mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_up_if_absent_thread_existing_reaction(self):
        """Test insert_up_if_absent returns False for existing thread reaction."""
        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.mock_db.transaction = Mock(return_value=mock_transaction)
        
        # Mock database responses - ON CONFLICT DO NOTHING returns 0 rows affected
        self.mock_db.execute = AsyncMock(return_value="INSERT 0 0")  # 0 rows affected
        
        result = await self.repo.insert_up_if_absent("thread", "thr_01H0000000000000000000000", "usr_01H0000000000000000000000")
        
        assert result is False
        # Should only call execute once (INSERT), no UPDATE since no rows affected
        assert self.mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_insert_up_if_absent_comment_new_reaction(self):
        """Test insert_up_if_absent creates new comment reaction successfully."""
        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.mock_db.transaction = Mock(return_value=mock_transaction)
        
        # Mock database responses
        self.mock_db.execute = AsyncMock(return_value="INSERT 0 1")  # 1 row affected
        
        result = await self.repo.insert_up_if_absent("comment", "cmt_01H0000000000000000000000", "usr_01H0000000000000000000000")
        
        assert result is True
        # Verify execute was called twice (INSERT + UPDATE)
        assert self.mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_up_if_absent_comment_existing_reaction(self):
        """Test insert_up_if_absent returns False for existing comment reaction."""
        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.mock_db.transaction = Mock(return_value=mock_transaction)
        
        # Mock database responses - ON CONFLICT DO NOTHING returns 0 rows affected
        self.mock_db.execute = AsyncMock(return_value="INSERT 0 0")  # 0 rows affected
        
        result = await self.repo.insert_up_if_absent("comment", "cmt_01H0000000000000000000000", "usr_01H0000000000000000000000")
        
        assert result is False
        # Should only call execute once (INSERT), no UPDATE since no rows affected
        assert self.mock_db.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_insert_up_if_absent_invalid_target_type(self):
        """Test insert_up_if_absent raises error for invalid target type."""
        with pytest.raises(ValueError):
            await self.repo.insert_up_if_absent("invalid", "thr_01H0000000000000000000000", "usr_01H0000000000000000000000")

    # Tests for P2-API-Repo-Reactions-UpsertSave functionality
    @pytest.mark.asyncio
    async def test_insert_save_if_absent_thread_new_reaction(self):
        """Test insert_save_if_absent creates new thread save reaction successfully."""
        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.mock_db.transaction = Mock(return_value=mock_transaction)
        
        # Mock database responses
        self.mock_db.execute = AsyncMock(return_value="INSERT 0 1")  # 1 row affected
        
        result = await self.repo.insert_save_if_absent("thr_01H0000000000000000000000", "usr_01H0000000000000000000000")
        
        assert result is True
        # Verify execute was called twice (INSERT + UPDATE threads.save_count)
        assert self.mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_insert_save_if_absent_thread_existing_reaction(self):
        """Test insert_save_if_absent returns False for existing thread save reaction."""
        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        self.mock_db.transaction = Mock(return_value=mock_transaction)
        
        # Mock database responses - ON CONFLICT DO NOTHING returns 0 rows affected
        self.mock_db.execute = AsyncMock(return_value="INSERT 0 0")  # 0 rows affected
        
        result = await self.repo.insert_save_if_absent("thr_01H0000000000000000000000", "usr_01H0000000000000000000000")
        
        assert result is False
        # Should only call execute once (INSERT), no UPDATE since no rows affected
        assert self.mock_db.execute.call_count == 1