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


def test_comment_service_has_list_method():
    """Test that CommentService has list_comments method."""
    service = CommentService(db=None)
    assert hasattr(service, "list_comments")
    
    import inspect
    sig = inspect.signature(service.list_comments)
    params = list(sig.parameters.keys())
    
    # Should be async method
    assert inspect.iscoroutinefunction(service.list_comments)
    
    # Check required parameters exist
    assert "thread_id" in params
    assert "current_user_id" in params
    assert "cursor" in params


def test_list_comments_success():
    """Test successful comment listing."""
    from datetime import datetime, timezone
    mock_db = AsyncMock()
    service = CommentService(db=mock_db)
    
    # Mock repository response
    service._repo = AsyncMock()
    service._repo.list_comments_by_thread = AsyncMock(return_value=[
        {
            "id": "cmt_01HX123456789ABCDEFGHJKMNP",
            "body": "First comment",
            "up_count": 2,
            "created_at": datetime(2025, 8, 9, 6, 0, 0, tzinfo=timezone.utc),
            "author_faculty": "理学部",
            "author_year": 2
        },
        {
            "id": "cmt_01HX123456789ABCDEFGHJKMNQ", 
            "body": "Second comment",
            "up_count": 1,
            "created_at": datetime(2025, 8, 9, 7, 0, 0, tzinfo=timezone.utc),
            "author_faculty": None,
            "author_year": None
        }
    ])
    
    async def run_test():
        result = await service.list_comments(
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            current_user_id="usr_01HX123456789ABCDEFGHJKMNP",
            cursor=None
        )
        
        # Should return PaginatedComments
        assert hasattr(result, "items")
        assert hasattr(result, "nextCursor")
        assert len(result.items) == 2
        
        # Check first comment
        comment1 = result.items[0]
        assert comment1.id == "cmt_01HX123456789ABCDEFGHJKMNP"
        assert comment1.body == "First comment"
        assert comment1.upCount == 2
        assert comment1.hasImage == False
        assert comment1.authorAffiliation.faculty == "理学部"
        assert comment1.authorAffiliation.year == 2
        
        # Check second comment
        comment2 = result.items[1]
        assert comment2.id == "cmt_01HX123456789ABCDEFGHJKMNQ"
        assert comment2.body == "Second comment"
        assert comment2.upCount == 1
        assert comment2.authorAffiliation is None
        
        # Should call repository
        service._repo.list_comments_by_thread.assert_called_once_with(
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            anchor_created_at=None,
            anchor_id=None,
            limit=20
        )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()


def test_list_comments_with_cursor():
    """Test comment listing with cursor pagination."""
    from app.util.cursor import encode_cursor
    from datetime import datetime, timezone
    mock_db = AsyncMock()
    service = CommentService(db=mock_db)
    
    service._repo = AsyncMock()
    service._repo.list_comments_by_thread = AsyncMock(return_value=[])
    
    async def run_test():
        # Create cursor
        cursor_obj = {
            "v": 1,
            "createdAt": "2025-08-09T07:00:00Z",
            "id": "cmt_01HX123456789ABCDEFGHJKMNP"
        }
        cursor = encode_cursor(cursor_obj)
        
        await service.list_comments(
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            current_user_id="usr_01HX123456789ABCDEFGHJKMNP",
            cursor=cursor
        )
        
        # Should call repository with cursor data
        service._repo.list_comments_by_thread.assert_called_once()
        call_args = service._repo.list_comments_by_thread.call_args
        assert call_args.kwargs["anchor_created_at"] is not None
        assert call_args.kwargs["anchor_id"] == "cmt_01HX123456789ABCDEFGHJKMNP"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()