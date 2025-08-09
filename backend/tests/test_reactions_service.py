"""Tests for ReactionService."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.reactions_service import ReactionService
from app.util.errors import ValidationException, ConflictException


class TestReactionService:
    """Test suite for ReactionService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = AsyncMock()
        self.service = ReactionService(self.mock_db)
    
    def test_reaction_service_instantiation(self):
        """Test that ReactionService can be instantiated."""
        service = ReactionService(self.mock_db)
        assert service is not None
        assert hasattr(service, '_db')
    
    @pytest.mark.asyncio
    async def test_react_comment_up_success(self):
        """Test successful comment up reaction."""
        # Mock repository
        from app.repositories.reactions_repo import ReactionRepository
        mock_repo = AsyncMock(spec=ReactionRepository)
        mock_repo.insert_up_if_absent = AsyncMock(return_value=True)  # New reaction inserted
        
        # Mock repository constructor
        with patch('app.services.reactions_service.ReactionRepository', return_value=mock_repo):
            result = await self.service.react_comment_up(
                user_id="usr_01H0000000000000000000000X",
                comment_id="cmt_01H0000000000000000000000X"
            )
        
        # Should return None for 204 No Content
        assert result is None
        
        # Verify repository was called with correct parameters
        mock_repo.insert_up_if_absent.assert_called_once_with(
            target_type="comment",
            target_id="cmt_01H0000000000000000000000X",
            user_id="usr_01H0000000000000000000000X"
        )
    
    @pytest.mark.asyncio
    async def test_react_comment_up_conflict(self):
        """Test comment up reaction when already exists (409 Conflict)."""
        # Mock repository
        from app.repositories.reactions_repo import ReactionRepository
        mock_repo = AsyncMock(spec=ReactionRepository)
        mock_repo.insert_up_if_absent = AsyncMock(return_value=False)  # Reaction already exists
        
        # Mock repository constructor
        with patch('app.services.reactions_service.ReactionRepository', return_value=mock_repo):
            with pytest.raises(ConflictException) as exc_info:
                await self.service.react_comment_up(
                    user_id="usr_01H0000000000000000000000X",
                    comment_id="cmt_01H0000000000000000000000X"
                )
        
        # Verify correct error message
        assert "already reacted" in str(exc_info.value).lower()
        
        # Verify repository was called
        mock_repo.insert_up_if_absent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_react_comment_up_invalid_comment_id_format(self):
        """Test comment up reaction with invalid comment ID format."""
        # Invalid format (not cmt_*)
        with pytest.raises(ValidationException) as exc_info:
            await self.service.react_comment_up(
                user_id="usr_01H0000000000000000000000X",
                comment_id="invalid_comment_id"
            )
        
        assert "invalid comment id" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_react_comment_up_malformed_comment_id(self):
        """Test comment up reaction with malformed comment ID."""
        # Correct prefix but wrong length
        with pytest.raises(ValidationException) as exc_info:
            await self.service.react_comment_up(
                user_id="usr_01H0000000000000000000000X",
                comment_id="cmt_invalid"
            )
        
        assert "invalid comment id" in str(exc_info.value).lower()
    
    def test_is_valid_comment_id_method(self):
        """Test comment ID validation method."""
        # Valid comment IDs (26 characters after prefix)
        assert self.service._is_valid_comment_id("cmt_01H0000000000000000000000X")
        assert self.service._is_valid_comment_id("cmt_01HX123456789ABCDEFGHJKMNP")
        
        # Invalid comment IDs
        assert not self.service._is_valid_comment_id("")
        assert not self.service._is_valid_comment_id("invalid")
        assert not self.service._is_valid_comment_id("thr_01H0000000000000000000000X")  # Wrong prefix
        assert not self.service._is_valid_comment_id("cmt_")  # Too short
        assert not self.service._is_valid_comment_id("cmt_invalid")  # Invalid ULID
        assert not self.service._is_valid_comment_id("cmt_01H0000000000000000000000XX")  # Too long
    
    # Tests for P2-API-Service-Reactions-ThreadUp functionality
    @pytest.mark.asyncio
    async def test_react_thread_up_success(self):
        """Test successful thread up reaction."""
        # Mock repository
        from app.repositories.reactions_repo import ReactionRepository
        mock_repo = AsyncMock(spec=ReactionRepository)
        mock_repo.insert_up_if_absent = AsyncMock(return_value=True)  # New reaction inserted
        
        # Mock repository constructor
        with patch('app.services.reactions_service.ReactionRepository', return_value=mock_repo):
            result = await self.service.react_thread_up(
                user_id="usr_01H0000000000000000000000X",
                thread_id="thr_01H0000000000000000000000X"
            )
        
        # Should return None for 204 No Content
        assert result is None
        
        # Verify repository was called with correct parameters
        mock_repo.insert_up_if_absent.assert_called_once_with(
            target_type="thread",
            target_id="thr_01H0000000000000000000000X",
            user_id="usr_01H0000000000000000000000X"
        )
    
    @pytest.mark.asyncio
    async def test_react_thread_up_conflict(self):
        """Test thread up reaction when already exists (409 Conflict)."""
        # Mock repository
        from app.repositories.reactions_repo import ReactionRepository
        mock_repo = AsyncMock(spec=ReactionRepository)
        mock_repo.insert_up_if_absent = AsyncMock(return_value=False)  # Reaction already exists
        
        # Mock repository constructor
        with patch('app.services.reactions_service.ReactionRepository', return_value=mock_repo):
            with pytest.raises(ConflictException) as exc_info:
                await self.service.react_thread_up(
                    user_id="usr_01H0000000000000000000000X",
                    thread_id="thr_01H0000000000000000000000X"
                )
        
        # Verify correct error message
        assert "already reacted" in str(exc_info.value).lower()
        
        # Verify repository was called
        mock_repo.insert_up_if_absent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_react_thread_up_invalid_thread_id_format(self):
        """Test thread up reaction with invalid thread ID format."""
        # Invalid format (not thr_*)
        with pytest.raises(ValidationException) as exc_info:
            await self.service.react_thread_up(
                user_id="usr_01H0000000000000000000000X",
                thread_id="invalid_thread_id"
            )
        
        assert "invalid thread id" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_react_thread_up_malformed_thread_id(self):
        """Test thread up reaction with malformed thread ID."""
        # Correct prefix but wrong length
        with pytest.raises(ValidationException) as exc_info:
            await self.service.react_thread_up(
                user_id="usr_01H0000000000000000000000X",
                thread_id="thr_invalid"
            )
        
        assert "invalid thread id" in str(exc_info.value).lower()
    
    def test_is_valid_thread_id_method(self):
        """Test thread ID validation method."""
        # Valid thread IDs (26 characters after prefix)
        assert self.service._is_valid_thread_id("thr_01H0000000000000000000000X")
        assert self.service._is_valid_thread_id("thr_01HX123456789ABCDEFGHJKMNP")
        
        # Invalid thread IDs
        assert not self.service._is_valid_thread_id("")
        assert not self.service._is_valid_thread_id("invalid")
        assert not self.service._is_valid_thread_id("cmt_01H0000000000000000000000X")  # Wrong prefix
        assert not self.service._is_valid_thread_id("thr_")  # Too short
        assert not self.service._is_valid_thread_id("thr_invalid")  # Invalid ULID
        assert not self.service._is_valid_thread_id("thr_01H0000000000000000000000XX")  # Too long