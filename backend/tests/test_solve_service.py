"""Tests for solve service layer."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.solve_service import SolveService
from app.util.errors import ValidationException, NotFoundException, ForbiddenException


class MockAcquire:
    """Mock async context manager for database connections."""
    def __init__(self, connection):
        self.connection = connection
    
    async def __aenter__(self):
        return self.connection
    
    async def __aexit__(self, *args):
        pass


class TestSolveService:
    """Test class for SolveService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = AsyncMock()
        self.service = SolveService(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_set_solved_comment_success(self):
        """Test successful comment solve setting."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - question type with same author
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "Test question",
            "body": "Test question body",
            "solved_comment_id": None,
            "deleted_at": None
        }
        
        # Mock comment data - exists and not deleted
        comment_data = {
            "id": comment_id,
            "thread_id": thread_id,
            "author_id": "usr_OTHER",
            "body": "Test answer",
            "deleted_at": None
        }
        
        # Set up mocks
        self.mock_db.fetchrow = AsyncMock()
        self.mock_db.fetchrow.side_effect = [
            thread_data,  # thread lookup
            comment_data  # comment lookup
        ]
        self.mock_db.execute = AsyncMock()  # for UPDATE query
        
        # Execute method
        result = await self.service.set_solved_comment(
            user_id=user_id,
            thread_id=thread_id,
            comment_id=comment_id
        )
        
        # Verify result is None (204 No Content)
        assert result is None
        
        # Verify database calls
        assert self.mock_db.fetchrow.call_count == 2
        self.mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_solved_comment_thread_not_found(self):
        """Test solve setting with non-existent thread."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_NONEXISTENT"
        comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread not found
        self.mock_db.fetchrow = AsyncMock(return_value=None)
        
        # Should raise NotFoundException
        with pytest.raises(NotFoundException, match="Thread not found"):
            await self.service.set_solved_comment(
                user_id=user_id,
                thread_id=thread_id,
                comment_id=comment_id
            )
    
    @pytest.mark.asyncio  
    async def test_set_solved_comment_thread_not_question_type(self):
        """Test solve setting on non-question thread."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - not a question type (assume we check tags)
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "General discussion",
            "body": "General discussion body",
            "solved_comment_id": None,
            "deleted_at": None
        }
        
        self.mock_db.fetchrow = AsyncMock(return_value=thread_data)
        
        # Mock the thread type check to return non-question type
        # For now, assume all threads without explicit question tag are general
        # Should raise ValidationException with NOT_APPLICABLE
        with pytest.raises(ValidationException) as exc_info:
            await self.service.set_solved_comment(
                user_id=user_id,
                thread_id=thread_id,
                comment_id=comment_id
            )
        
        # Check error details
        assert exc_info.value.details is not None
        assert exc_info.value.details[0]["reason"] == "NOT_APPLICABLE"
        assert exc_info.value.details[0]["field"] == "thread.tags"
    
    @pytest.mark.asyncio
    async def test_set_solved_comment_not_thread_owner(self):
        """Test solve setting by non-owner of thread."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - different author
        thread_data = {
            "id": thread_id,
            "author_id": "usr_DIFFERENT_OWNER",  # Different owner
            "title": "Test question",
            "body": "Test question body", 
            "solved_comment_id": None,
            "deleted_at": None
        }
        
        self.mock_db.fetchrow = AsyncMock(return_value=thread_data)
        
        # Should raise ForbiddenException
        with pytest.raises(ForbiddenException, match="Only thread author can set solved comment"):
            await self.service.set_solved_comment(
                user_id=user_id,
                thread_id=thread_id,
                comment_id=comment_id
            )
    
    @pytest.mark.asyncio
    async def test_set_solved_comment_comment_not_found(self):
        """Test solve setting with non-existent comment."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        comment_id = "cmt_NONEXISTENT"
        
        # Mock thread data - valid question thread
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "Test question",
            "body": "Test question body",
            "solved_comment_id": None,
            "deleted_at": None
        }
        
        # Mock comment not found
        self.mock_db.fetchrow = AsyncMock()
        self.mock_db.fetchrow.side_effect = [
            thread_data,  # thread found
            None          # comment not found
        ]
        
        # Should raise NotFoundException
        with pytest.raises(NotFoundException, match="Comment not found"):
            await self.service.set_solved_comment(
                user_id=user_id,
                thread_id=thread_id,
                comment_id=comment_id
            )
    
    @pytest.mark.asyncio
    async def test_set_solved_comment_comment_deleted(self):
        """Test solve setting on deleted comment."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - valid question thread
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "Test question", 
            "body": "Test question body",
            "solved_comment_id": None,
            "deleted_at": None
        }
        
        # Mock comment data - deleted
        comment_data = {
            "id": comment_id,
            "thread_id": thread_id,
            "author_id": "usr_OTHER",
            "body": "Test answer",
            "deleted_at": "2024-01-01T12:00:00Z"  # Comment is deleted
        }
        
        self.mock_db.fetchrow = AsyncMock()
        self.mock_db.fetchrow.side_effect = [
            thread_data,  # thread found
            comment_data  # comment found but deleted
        ]
        
        # Should raise NotFoundException for deleted comment
        with pytest.raises(NotFoundException, match="Comment not found"):
            await self.service.set_solved_comment(
                user_id=user_id,
                thread_id=thread_id,
                comment_id=comment_id
            )
    
    @pytest.mark.asyncio
    async def test_set_solved_comment_replace_existing(self):
        """Test solve setting replacing existing solved comment."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        old_solved_id = "cmt_OLD_SOLVED"
        
        # Mock thread data - already has solved comment
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "Test question",
            "body": "Test question body",
            "solved_comment_id": old_solved_id,  # Already has solved comment
            "deleted_at": None
        }
        
        # Mock comment data - new comment to be marked as solved
        comment_data = {
            "id": comment_id,
            "thread_id": thread_id,
            "author_id": "usr_OTHER",
            "body": "Better answer",
            "deleted_at": None
        }
        
        self.mock_db.fetchrow = AsyncMock()
        self.mock_db.fetchrow.side_effect = [
            thread_data,  # thread lookup
            comment_data  # comment lookup
        ]
        self.mock_db.execute = AsyncMock()  # for UPDATE query
        
        # Execute method
        result = await self.service.set_solved_comment(
            user_id=user_id,
            thread_id=thread_id,
            comment_id=comment_id
        )
        
        # Verify result is None (204 No Content)
        assert result is None
        
        # Verify database calls - should update solved_comment_id
        assert self.mock_db.fetchrow.call_count == 2
        self.mock_db.execute.assert_called_once()
        
        # Verify UPDATE query was called with new comment_id
        execute_call = self.mock_db.execute.call_args
        assert comment_id in execute_call[0]  # New comment_id should be in the query params
    
    @pytest.mark.asyncio
    async def test_clear_solved_comment_success(self):
        """Test successful solve clearing."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        solved_comment_id = "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - question type with solved comment
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "Test question",
            "body": "Test question body",
            "solved_comment_id": solved_comment_id,  # Has solved comment
            "deleted_at": None
        }
        
        # Set up mocks
        self.mock_db.fetchrow = AsyncMock(return_value=thread_data)
        self.mock_db.execute = AsyncMock()  # for UPDATE query
        
        # Execute method
        result = await self.service.clear_solved_comment(
            user_id=user_id,
            thread_id=thread_id
        )
        
        # Verify result is None (204 No Content)
        assert result is None
        
        # Verify database calls
        self.mock_db.fetchrow.assert_called_once()
        self.mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_solved_comment_thread_not_found(self):
        """Test solve clearing with non-existent thread."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_NONEXISTENT"
        
        # Mock thread not found
        self.mock_db.fetchrow = AsyncMock(return_value=None)
        
        # Should raise NotFoundException
        with pytest.raises(NotFoundException, match="Thread not found"):
            await self.service.clear_solved_comment(
                user_id=user_id,
                thread_id=thread_id
            )
    
    @pytest.mark.asyncio
    async def test_clear_solved_comment_thread_not_question_type(self):
        """Test solve clearing on non-question thread."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - not a question type
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "General discussion",
            "body": "General discussion body",
            "solved_comment_id": None,
            "deleted_at": None
        }
        
        self.mock_db.fetchrow = AsyncMock(return_value=thread_data)
        
        # Should raise ValidationException with NOT_APPLICABLE
        with pytest.raises(ValidationException) as exc_info:
            await self.service.clear_solved_comment(
                user_id=user_id,
                thread_id=thread_id
            )
        
        # Check error details
        assert exc_info.value.details is not None
        assert exc_info.value.details[0]["reason"] == "NOT_APPLICABLE"
        assert exc_info.value.details[0]["field"] == "thread.tags"
    
    @pytest.mark.asyncio
    async def test_clear_solved_comment_not_thread_owner(self):
        """Test solve clearing by non-owner of thread."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - different author
        thread_data = {
            "id": thread_id,
            "author_id": "usr_DIFFERENT_OWNER",  # Different owner
            "title": "Test question",
            "body": "Test question body", 
            "solved_comment_id": "cmt_SOME_COMMENT",
            "deleted_at": None
        }
        
        self.mock_db.fetchrow = AsyncMock(return_value=thread_data)
        
        # Should raise ForbiddenException
        with pytest.raises(ForbiddenException, match="Only thread author can clear solved comment"):
            await self.service.clear_solved_comment(
                user_id=user_id,
                thread_id=thread_id
            )
    
    @pytest.mark.asyncio
    async def test_clear_solved_comment_no_solved_comment(self):
        """Test solve clearing when no solved comment is set."""
        user_id = "usr_01HX123456789ABCDEFGHJKMNP"
        thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
        
        # Mock thread data - no solved comment
        thread_data = {
            "id": thread_id,
            "author_id": user_id,
            "title": "Test question",
            "body": "Test question body",
            "solved_comment_id": None,  # No solved comment
            "deleted_at": None
        }
        
        self.mock_db.fetchrow = AsyncMock(return_value=thread_data)
        
        # Should raise ValidationException for no solved comment to clear
        with pytest.raises(ValidationException, match="No solved comment to clear"):
            await self.service.clear_solved_comment(
                user_id=user_id,
                thread_id=thread_id
            )