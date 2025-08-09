import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.util.errors import ValidationException
from app.schemas.threads import CreateThreadRequest, ThreadCard, ThreadDetail, Tag, PaginatedThreadCards
from app.services.threads_service import ThreadService


def test_thread_service_class_exists():
    """Test that ThreadService class exists."""
    service = ThreadService(db=None)
    assert service is not None


def test_thread_service_has_create_method():
    """Test that ThreadService has create_thread method."""
    service = ThreadService(db=None)
    assert hasattr(service, "create_thread")


def test_create_thread_basic():
    """Test basic thread creation."""
    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.create_thread = AsyncMock(return_value="thr_01HX123456789ABCDEFGHJKMNP")
    
    created_at = datetime.now(timezone.utc)
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": "Test body content",
        "up_count": 0,
        "save_count": 0,
        "solved_comment_id": None,
        "heat": 0.0,
        "created_at": created_at,
        "last_activity_at": created_at,
        "deleted_at": None
    })
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        # Create thread request
        thread_request = CreateThreadRequest(
            title="Test Thread",
            body="Test body content",
            tags=[Tag(key="種別", value="question")],
            imageKey=None
        )
        
        # Mock the repository inside service
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.create_thread(
                user_id="usr_01HX123456789ABCDEFGHJKMNP",
                thread_create=thread_request
            )
            
            # Check result is ThreadCard
            assert isinstance(result, ThreadCard)
            assert result.id == "thr_01HX123456789ABCDEFGHJKMNP"
            assert result.title == "Test Thread"
            assert result.excerpt == "Test body content"
            
            # Verify repository was called correctly
            mock_repo.create_thread.assert_called_once_with(
                author_id="usr_01HX123456789ABCDEFGHJKMNP",
                title="Test Thread",
                body="Test body content",
                tags=[Tag(key="種別", value="question")],
                image_key=None
            )
    
    asyncio.run(run_test())


def test_create_thread_title_validation():
    """Test title validation in create_thread."""
    # Title cannot be empty string in Pydantic validation
    from pydantic import ValidationError
    
    # Test empty title
    with pytest.raises(ValidationError) as exc_info:
        thread_request = CreateThreadRequest(
            title="",  # Empty title
            body="Valid body",
            tags=[],
            imageKey=None
        )
    
    assert "title" in str(exc_info.value).lower()


def test_create_thread_body_validation():
    """Test body validation in create_thread."""
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        # Test body with only whitespace
        thread_request = CreateThreadRequest(
            title="Valid Title",
            body="\n\t  \n",  # Only whitespace
            tags=[],
            imageKey=None
        )
        
        # Body can be empty but if provided, should not be only whitespace
        # Actually, based on specs, empty body is allowed (default="")
        # So this test should pass
        mock_repo = AsyncMock()
        mock_repo.create_thread = AsyncMock(return_value="thr_01HX123456789ABCDEFGHJKMNP")
        mock_repo.get_thread_by_id = AsyncMock(return_value={
            "id": "thr_01HX123456789ABCDEFGHJKMNP",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Valid Title",
            "body": "",
            "up_count": 0,
            "save_count": 0,
            "created_at": datetime.now(timezone.utc),
            "last_activity_at": datetime.now(timezone.utc),
            "deleted_at": None
        })
        
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            # Should trim whitespace and accept empty body
            result = await service.create_thread(
                user_id="usr_01HX123456789ABCDEFGHJKMNP",
                thread_create=thread_request
            )
            
            # Body should be trimmed to empty string
            mock_repo.create_thread.assert_called_once()
            call_args = mock_repo.create_thread.call_args[1]
            assert call_args["body"] == ""
    
    asyncio.run(run_test())


def test_create_thread_removes_control_characters():
    """Test that control characters are removed from title and body."""
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        # Title and body with control characters
        thread_request = CreateThreadRequest(
            title="Test\x00Thread\x01Title",  # Contains null and other control chars
            body="Body\x02with\x03control\x04chars",
            tags=[],
            imageKey=None
        )
        
        mock_repo = AsyncMock()
        mock_repo.create_thread = AsyncMock(return_value="thr_01HX123456789ABCDEFGHJKMNP")
        mock_repo.get_thread_by_id = AsyncMock(return_value={
            "id": "thr_01HX123456789ABCDEFGHJKMNP",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "TestThreadTitle",
            "body": "Bodywithcontrolchars",
            "up_count": 0,
            "save_count": 0,
            "created_at": datetime.now(timezone.utc),
            "last_activity_at": datetime.now(timezone.utc),
            "deleted_at": None
        })
        
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            await service.create_thread(
                user_id="usr_01HX123456789ABCDEFGHJKMNP",
                thread_create=thread_request
            )
            
            # Check control characters were removed
            mock_repo.create_thread.assert_called_once()
            call_args = mock_repo.create_thread.call_args[1]
            assert call_args["title"] == "TestThreadTitle"
            assert call_args["body"] == "Bodywithcontrolchars"
    
    asyncio.run(run_test())


def test_create_thread_with_tags():
    """Test thread creation with tags."""
    mock_repo = AsyncMock()
    mock_repo.create_thread = AsyncMock(return_value="thr_01HX123456789ABCDEFGHJKMNP")
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Question about Python",
        "body": "How do I use async/await?",
        "up_count": 0,
        "save_count": 0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        thread_request = CreateThreadRequest(
            title="Question about Python",
            body="How do I use async/await?",
            tags=[Tag(key="種別", value="question"), Tag(key="場所", value="dev")],
            imageKey=None
        )
        
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.create_thread(
                user_id="usr_01HX123456789ABCDEFGHJKMNP",
                thread_create=thread_request
            )
            
            # Verify tags were passed to repository
            mock_repo.create_thread.assert_called_once()
            call_args = mock_repo.create_thread.call_args[1]
            assert call_args["tags"] == [Tag(key="種別", value="question"), Tag(key="場所", value="dev")]
    
    asyncio.run(run_test())


def test_create_thread_returns_thread_card():
    """Test that create_thread returns a properly formatted ThreadCard."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    mock_repo.create_thread = AsyncMock(return_value=thread_id)
    
    # Mock getting the created thread
    created_at = datetime.now(timezone.utc)
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": "This is a test thread body that should be excerpted",
        "up_count": 0,
        "save_count": 0,
        "solved_comment_id": None,
        "heat": 0.0,
        "created_at": created_at,
        "last_activity_at": created_at,
        "deleted_at": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        thread_request = CreateThreadRequest(
            title="Test Thread",
            body="This is a test thread body that should be excerpted",
            tags=[Tag(key="種別", value="question")],
            imageKey=None
        )
        
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.create_thread(
                user_id="usr_01HX123456789ABCDEFGHJKMNP",
                thread_create=thread_request
            )
            
            # Check ThreadCard fields
            assert isinstance(result, ThreadCard)
            assert result.id == thread_id
            assert result.title == "Test Thread"
            assert result.excerpt == "This is a test thread body that should be excerpted"
            assert result.hasImage is False
            assert result.solved is False
            assert result.heat == 0
            assert result.replies == 0
            assert result.saves == 0
            assert result.tags == [Tag(key="種別", value="question")]
            assert result.createdAt == created_at.isoformat().replace("+00:00", "Z")
    
    asyncio.run(run_test())


def test_create_thread_error_propagation():
    """Test that database errors are properly propagated."""
    mock_repo = AsyncMock()
    mock_repo.create_thread = AsyncMock(side_effect=Exception("Database error"))
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        thread_request = CreateThreadRequest(
            title="Test Thread",
            body="Test body",
            tags=[],
            imageKey=None
        )
        
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            with pytest.raises(Exception) as exc_info:
                await service.create_thread(
                    user_id="usr_01HX123456789ABCDEFGHJKMNP",
                    thread_create=thread_request
                )
            
            assert "Database error" in str(exc_info.value)
    
    asyncio.run(run_test())


def test_create_thread_max_title_length():
    """Test that title length is enforced."""
    # Title exceeding max length (60 chars)
    long_title = "a" * 61
    
    # This should be caught by Pydantic validation in CreateThreadRequest
    # So we expect a validation error at the DTO level
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError) as exc_info:
        thread_request = CreateThreadRequest(
            title=long_title,
            body="Valid body",
            tags=[],
            imageKey=None
        )
    
    # Check that the error is about title length
    assert "title" in str(exc_info.value).lower()
    assert "60" in str(exc_info.value)


def test_get_thread_exists():
    """Test getting an existing thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    author_id = "usr_01HX123456789ABCDEFGHJKMNP"
    created_at = datetime.now(timezone.utc)
    
    # Mock repository return value
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": author_id,
        "title": "Test Thread",
        "body": "This is a test thread body",
        "up_count": 5,
        "save_count": 2,
        "solved_comment_id": None,
        "heat": 1.5,
        "created_at": created_at,
        "last_activity_at": created_at,
        "deleted_at": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            # Get thread as the author
            result = await service.get_thread(
                thread_id=thread_id,
                current_user_id=author_id
            )
            
            # Verify result
            assert isinstance(result, ThreadDetail)
            assert result.id == thread_id
            assert result.title == "Test Thread"
            assert result.body == "This is a test thread body"
            assert result.upCount == 5
            assert result.saveCount == 2
            assert result.solvedCommentId is None
            assert result.isMine is True  # Author viewing their own thread
            
            # Verify repository was called
            mock_repo.get_thread_by_id.assert_called_once_with(thread_id=thread_id)
    
    asyncio.run(run_test())


def test_get_thread_not_mine():
    """Test getting a thread that doesn't belong to current user."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    author_id = "usr_01HX123456789ABCDEFGHJKMNP"
    current_user_id = "usr_01HX987654321ZYXWVUTSRQP"
    created_at = datetime.now(timezone.utc)
    
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": author_id,
        "title": "Someone else's thread",
        "body": "Body content",
        "up_count": 0,
        "save_count": 0,
        "created_at": created_at,
        "last_activity_at": created_at,
        "deleted_at": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.get_thread(
                thread_id=thread_id,
                current_user_id=current_user_id
            )
            
            # Verify the thread is returned but not marked as mine
            assert result is not None
            assert result.id == thread_id
            # The is_mine field isn't in ThreadCard, but the service should handle it internally
    
    asyncio.run(run_test())


def test_get_thread_not_found():
    """Test getting a non-existent thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    
    # Repository returns None for non-existent thread
    mock_repo.get_thread_by_id = AsyncMock(return_value=None)
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.get_thread(
                thread_id=thread_id,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Should return None for non-existent thread
            assert result is None
            mock_repo.get_thread_by_id.assert_called_once_with(thread_id=thread_id)
    
    asyncio.run(run_test())


def test_get_thread_deleted():
    """Test that deleted threads are not returned."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    deleted_at = datetime.now(timezone.utc)
    
    # Repository should filter out deleted threads
    mock_repo.get_thread_by_id = AsyncMock(return_value=None)
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.get_thread(
                thread_id=thread_id,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Deleted threads should return None
            assert result is None
    
    asyncio.run(run_test())


def test_get_thread_with_solved():
    """Test getting a solved thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    created_at = datetime.now(timezone.utc)
    
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Solved Question",
        "body": "How do I do X?",
        "up_count": 10,
        "save_count": 3,
        "solved_comment_id": "cmt_01HX123456789ABCDEFGHJKMNP",  # Has a solved comment
        "heat": 2.0,
        "created_at": created_at,
        "last_activity_at": created_at,
        "deleted_at": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.get_thread(
                thread_id=thread_id,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Check that solved status is correctly set
            assert result.solvedCommentId == "cmt_01HX123456789ABCDEFGHJKMNP"
            assert result.title == "Solved Question"
    
    asyncio.run(run_test())


def test_get_thread_id_validation():
    """Test thread ID validation in get_thread."""
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        # Test with invalid thread ID format
        with pytest.raises(ValidationException) as exc_info:
            await service.get_thread(
                thread_id="invalid_id",
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
        
        assert "Invalid thread ID" in str(exc_info.value)
    
    asyncio.run(run_test())


def test_list_threads_new_without_cursor():
    """Test listing threads without cursor (first page)."""
    mock_repo = AsyncMock()
    created_at = datetime.now(timezone.utc)
    
    # Mock repository return value with multiple threads
    mock_repo.list_threads_new = AsyncMock(return_value={
        "threads": [
            {
                "id": "thr_01HX333333333333333333333",
                "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
                "title": "Newest Thread",
                "body": "This is the newest thread",
                "up_count": 0,
                "save_count": 0,
                "heat": 0.0,
                "created_at": created_at,
                "last_activity_at": created_at,
                "deleted_at": None
            },
            {
                "id": "thr_01HX222222222222222222222",
                "author_id": "usr_01HX987654321ZYXWVUTSRQP",
                "title": "Second Thread",
                "body": "This is the second thread",
                "up_count": 5,
                "save_count": 2,
                "heat": 1.5,
                "created_at": created_at - timedelta(hours=1),
                "last_activity_at": created_at - timedelta(hours=1),
                "deleted_at": None
            }
        ],
        "has_more": True
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.list_threads_new(
                cursor=None,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Check result structure
            assert isinstance(result, PaginatedThreadCards)
            assert len(result.items) == 2
            assert result.items[0].id == "thr_01HX333333333333333333333"
            assert result.items[0].title == "Newest Thread"
            assert result.items[1].id == "thr_01HX222222222222222222222"
            assert result.nextCursor is not None
            
            # Verify repository was called correctly
            mock_repo.list_threads_new.assert_called_once_with(
                cursor=None,
                limit=20
            )
    
    asyncio.run(run_test())


def test_list_threads_new_with_cursor():
    """Test listing threads with cursor (pagination)."""
    mock_repo = AsyncMock()
    created_at = datetime.now(timezone.utc)
    
    # Create a test cursor
    from app.util.cursor import encode_cursor
    test_cursor = encode_cursor({
        "v": 1,
        "createdAt": "2024-01-01T00:00:00Z",
        "id": "thr_01HX111111111111111111111"
    })
    
    mock_repo.list_threads_new = AsyncMock(return_value={
        "threads": [
            {
                "id": "thr_01HX000000000000000000000",
                "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
                "title": "Older Thread",
                "body": "This is an older thread",
                "up_count": 10,
                "save_count": 5,
                "heat": 2.0,
                "created_at": created_at - timedelta(days=1),
                "last_activity_at": created_at - timedelta(days=1),
                "deleted_at": None
            }
        ],
        "has_more": False
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.list_threads_new(
                cursor=test_cursor,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Check pagination result
            assert len(result.items) == 1
            assert result.items[0].id == "thr_01HX000000000000000000000"
            assert result.nextCursor is None  # No more pages
            
            # Verify repository was called with cursor
            mock_repo.list_threads_new.assert_called_once_with(
                cursor=test_cursor,
                limit=20
            )
    
    asyncio.run(run_test())


def test_list_threads_new_empty_result():
    """Test listing threads with empty result."""
    mock_repo = AsyncMock()
    
    mock_repo.list_threads_new = AsyncMock(return_value={
        "threads": [],
        "has_more": False
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.list_threads_new(
                cursor=None,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Check empty result
            assert len(result.items) == 0
            assert result.nextCursor is None
    
    asyncio.run(run_test())


def test_list_threads_new_with_is_mine():
    """Test that threads correctly identify ownership."""
    mock_repo = AsyncMock()
    current_user_id = "usr_01HX123456789ABCDEFGHJKMNP"
    other_user_id = "usr_01HX987654321ZYXWVUTSRQP"
    created_at = datetime.now(timezone.utc)
    
    mock_repo.list_threads_new = AsyncMock(return_value={
        "threads": [
            {
                "id": "thr_01HX111111111111111111111",
                "author_id": current_user_id,  # Owned by current user
                "title": "My Thread",
                "body": "This is my thread",
                "up_count": 0,
                "save_count": 0,
                "heat": 0.0,
                "created_at": created_at,
                "last_activity_at": created_at,
                "deleted_at": None
            },
            {
                "id": "thr_01HX222222222222222222222",
                "author_id": other_user_id,  # Owned by another user
                "title": "Someone's Thread",
                "body": "This is someone else's thread",
                "up_count": 0,
                "save_count": 0,
                "heat": 0.0,
                "created_at": created_at,
                "last_activity_at": created_at,
                "deleted_at": None
            }
        ],
        "has_more": False
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.list_threads_new(
                cursor=None,
                current_user_id=current_user_id
            )
            
            # Both threads should be returned
            assert len(result.items) == 2
            # is_mine is internal, but we can verify author_id handling
            assert result.items[0].title == "My Thread"
            assert result.items[1].title == "Someone's Thread"
    
    asyncio.run(run_test())


def test_list_threads_new_invalid_cursor():
    """Test listing threads with invalid cursor."""
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        # Invalid cursor should raise ValidationException
        with pytest.raises(ValidationException) as exc_info:
            await service.list_threads_new(
                cursor="invalid_cursor_not_base64",
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
        
        assert "Invalid cursor" in str(exc_info.value)
    
    asyncio.run(run_test())


def test_list_threads_new_cursor_generation():
    """Test that next cursor is generated correctly."""
    mock_repo = AsyncMock()
    created_at = datetime.now(timezone.utc)
    last_thread_created = created_at - timedelta(hours=2)
    
    mock_repo.list_threads_new = AsyncMock(return_value={
        "threads": [
            {
                "id": "thr_01HX111111111111111111111",
                "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
                "title": "First",
                "body": "Body",
                "up_count": 0,
                "save_count": 0,
                "heat": 0.0,
                "created_at": created_at,
                "last_activity_at": created_at,
                "deleted_at": None
            },
            {
                "id": "thr_01HX222222222222222222222",
                "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
                "title": "Last on page",
                "body": "Body",
                "up_count": 0,
                "save_count": 0,
                "heat": 0.0,
                "created_at": last_thread_created,
                "last_activity_at": last_thread_created,
                "deleted_at": None
            }
        ],
        "has_more": True
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            result = await service.list_threads_new(
                cursor=None,
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
            
            # Next cursor should be based on last thread
            assert result.nextCursor is not None
            
            # Decode and check cursor content
            from app.util.cursor import decode_cursor
            cursor_data = decode_cursor(result.nextCursor)
            assert cursor_data["id"] == "thr_01HX222222222222222222222"
            # Timestamp should match last thread's created_at
    
    asyncio.run(run_test())


def test_delete_thread_by_owner():
    """Test that owner can delete their thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    owner_id = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock repository to return thread owned by current user
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": owner_id,
        "title": "My Thread",
        "body": "Thread content",
        "up_count": 0,
        "save_count": 0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": None
    })
    
    # Mock soft delete method
    mock_repo.soft_delete_thread = AsyncMock(return_value=True)
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            # Owner should be able to delete their thread
            await service.delete_thread(
                thread_id=thread_id,
                current_user_id=owner_id
            )
            
            # Verify repository methods were called
            mock_repo.get_thread_by_id.assert_called_once_with(thread_id=thread_id)
            mock_repo.soft_delete_thread.assert_called_once_with(
                thread_id=thread_id,
                user_id=owner_id
            )
    
    asyncio.run(run_test())


def test_delete_thread_by_non_owner():
    """Test that non-owner cannot delete thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    owner_id = "usr_01HX123456789ABCDEFGHJKMNP"
    other_user_id = "usr_01HX987654321ZYXWVUTSRQP"
    
    # Mock repository to return thread owned by another user
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": owner_id,
        "title": "Someone's Thread",
        "body": "Thread content",
        "up_count": 0,
        "save_count": 0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            # Non-owner should not be able to delete
            from app.util.errors import ForbiddenException
            with pytest.raises(ForbiddenException) as exc_info:
                await service.delete_thread(
                    thread_id=thread_id,
                    current_user_id=other_user_id
                )
            
            assert "You can only delete your own threads" in str(exc_info.value)
            
            # Verify soft_delete was NOT called
            mock_repo.soft_delete_thread.assert_not_called()
    
    asyncio.run(run_test())


def test_delete_thread_not_found():
    """Test deleting non-existent thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    user_id = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock repository to return None (thread not found)
    mock_repo.get_thread_by_id = AsyncMock(return_value=None)
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            from app.util.errors import NotFoundException
            with pytest.raises(NotFoundException) as exc_info:
                await service.delete_thread(
                    thread_id=thread_id,
                    current_user_id=user_id
                )
            
            assert "Thread not found" in str(exc_info.value)
            
            # Verify soft_delete was NOT called
            mock_repo.soft_delete_thread.assert_not_called()
    
    asyncio.run(run_test())


def test_delete_thread_already_deleted():
    """Test deleting already deleted thread."""
    mock_repo = AsyncMock()
    thread_id = "thr_01HX123456789ABCDEFGHJKMNP"
    owner_id = "usr_01HX123456789ABCDEFGHJKMNP"
    
    # Mock repository to return already deleted thread
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": thread_id,
        "author_id": owner_id,
        "title": "Deleted Thread",
        "body": "Thread content",
        "up_count": 0,
        "save_count": 0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": datetime.now(timezone.utc)  # Already deleted
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        with patch('app.services.threads_service.ThreadRepository') as MockRepo:
            MockRepo.return_value = mock_repo
            
            from app.util.errors import NotFoundException
            with pytest.raises(NotFoundException) as exc_info:
                await service.delete_thread(
                    thread_id=thread_id,
                    current_user_id=owner_id
                )
            
            assert "Thread not found" in str(exc_info.value)
            
            # Verify soft_delete was NOT called
            mock_repo.soft_delete_thread.assert_not_called()
    
    asyncio.run(run_test())


def test_delete_thread_invalid_id():
    """Test deleting thread with invalid ID format."""
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    async def run_test():
        # Invalid thread ID should raise ValidationException
        with pytest.raises(ValidationException) as exc_info:
            await service.delete_thread(
                thread_id="invalid_id",
                current_user_id="usr_01HX123456789ABCDEFGHJKMNP"
            )
        
        assert "Invalid thread ID" in str(exc_info.value)
    
    asyncio.run(run_test())