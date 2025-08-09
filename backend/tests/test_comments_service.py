import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.comments_service import CommentService
from app.schemas.comments import CreateCommentRequest
from app.util.errors import ValidationException


def test_comment_service_class_exists():
    """Test that CommentService can be instantiated."""
    service = CommentService(db=None)
    assert service is not None


def test_comment_service_has_create_method():
    """Test that CommentService has create_comment method."""
    service = CommentService(db=None)
    assert hasattr(service, "create_comment")
    
    import inspect
    sig = inspect.signature(service.create_comment)
    params = list(sig.parameters.keys())
    
    # Should be async method
    assert inspect.iscoroutinefunction(service.create_comment)
    
    # Check required parameters exist
    assert "user_id" in params
    assert "thread_id" in params
    assert "dto" in params


def test_create_comment_success():
    """Test successful comment creation."""
    # Mock repository response
    mock_db = AsyncMock()
    
    service = CommentService(db=mock_db)
    
    # Mock repository's create_comment to return a comment ID
    service._repo = AsyncMock()
    service._repo.create_comment = AsyncMock(return_value="cmt_01HX123456789ABCDEFGHJKMNP")
    
    async def run_test():
        dto = CreateCommentRequest(
            body="This is a test comment",
            imageKey=None
        )
        
        result = await service.create_comment(
            user_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            dto=dto
        )
        
        # Should return CreatedResponse with the comment ID
        assert hasattr(result, "id")
        assert hasattr(result, "createdAt")
        assert result.id == "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Should call repository create_comment
        service._repo.create_comment.assert_called_once_with(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            body="This is a test comment",
            image_key=None
        )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()


def test_create_comment_validates_body():
    """Test that Pydantic validates body text at DTO level."""
    from pydantic import ValidationError
    
    # Test empty body - should fail at Pydantic level
    try:
        dto = CreateCommentRequest(body="", imageKey=None)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "String should have at least 1 character" in str(e)
    
    # Test successful validation with valid body
    dto = CreateCommentRequest(body="Valid comment", imageKey=None)
    assert dto.body == "Valid comment"


def test_create_comment_cleans_body():
    """Test that create_comment trims and cleans body text."""
    mock_db = AsyncMock()
    service = CommentService(db=mock_db)
    service._repo = AsyncMock()
    service._repo.create_comment = AsyncMock(return_value="cmt_01HX123456789ABCDEFGHJKMNP")
    
    async def run_test():
        # Test with whitespace and control characters
        dto = CreateCommentRequest(
            body="  \x00\x01Test comment with control chars\x7F  ",
            imageKey=None
        )
        
        await service.create_comment(
            user_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP", 
            dto=dto
        )
        
        # Should call repository with cleaned text
        service._repo.create_comment.assert_called_once()
        call_args = service._repo.create_comment.call_args
        assert call_args.kwargs["body"] == "Test comment with control chars"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()


def test_create_comment_validates_length():
    """Test that Pydantic validates body length at DTO level."""
    from pydantic import ValidationError
    
    # Test body too long (> 1000 chars) - should fail at Pydantic level
    long_body = "x" * 1001
    try:
        dto = CreateCommentRequest(body=long_body, imageKey=None)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "String should have at most 1000 characters" in str(e)
    
    # Test valid length
    valid_body = "x" * 1000
    dto = CreateCommentRequest(body=valid_body, imageKey=None)
    assert len(dto.body) == 1000


def test_create_comment_with_image_key():
    """Test comment creation with image key."""
    mock_db = AsyncMock()
    service = CommentService(db=mock_db)
    service._repo = AsyncMock()
    service._repo.create_comment = AsyncMock(return_value="cmt_01HX123456789ABCDEFGHJKMNP")
    
    async def run_test():
        dto = CreateCommentRequest(
            body="Comment with image",
            imageKey="uploads/2025/08/test.jpg"
        )
        
        await service.create_comment(
            user_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            dto=dto
        )
        
        # Should pass image_key to repository
        service._repo.create_comment.assert_called_once_with(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            body="Comment with image",
            image_key="uploads/2025/08/test.jpg"
        )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()