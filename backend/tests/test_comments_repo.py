import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.repositories.comments_repo import CommentRepository


def test_comments_repo_class_exists():
    """Test that CommentRepository can be instantiated."""
    repo = CommentRepository(db=None)
    assert repo is not None


def test_comments_repo_signatures():
    """Test that all required methods exist on CommentRepository."""
    repo = CommentRepository(db=None)
    assert hasattr(repo, "create_comment")
    assert hasattr(repo, "list_comments_by_thread")
    assert hasattr(repo, "soft_delete_comment")
    assert hasattr(repo, "get_comment_by_id")


def test_comment_id_helper_format():
    """Test that comment ID generation produces correct format."""
    from app.util.idgen import is_valid_id

    repo = CommentRepository(db=None)
    new_id = repo._generate_comment_id()
    assert new_id.startswith("cmt_")
    assert is_valid_id(new_id)


def test_timestamp_helper():
    """Test that timestamp helper produces ISO8601 UTC format."""
    repo = CommentRepository(db=None)
    timestamp = repo._now_utc()
    assert timestamp.endswith("Z")
    assert "T" in timestamp
    # Should be parseable as ISO format
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo == timezone.utc


def test_create_comment_signature():
    """Test create_comment method signature and basic validation."""
    repo = CommentRepository(db=MagicMock())

    # Test that method exists and has correct signature
    import inspect
    sig = inspect.signature(repo.create_comment)
    params = list(sig.parameters.keys())
    
    # Should be async method
    assert inspect.iscoroutinefunction(repo.create_comment)
    
    # Check required parameters exist
    assert "author_id" in params
    assert "thread_id" in params 
    assert "body" in params
    assert "image_key" in params


def test_list_comments_by_thread_signature():
    """Test list_comments_by_thread method signature."""
    repo = CommentRepository(db=MagicMock())

    import inspect
    sig = inspect.signature(repo.list_comments_by_thread)
    params = list(sig.parameters.keys())
    
    # Should be async method
    assert inspect.iscoroutinefunction(repo.list_comments_by_thread)
    
    # Check required parameters exist
    assert "thread_id" in params
    assert "anchor_created_at" in params
    assert "anchor_id" in params
    assert "limit" in params


def test_soft_delete_comment_signature():
    """Test soft_delete_comment method signature."""
    repo = CommentRepository(db=MagicMock())

    import inspect
    sig = inspect.signature(repo.soft_delete_comment)
    params = list(sig.parameters.keys())
    
    # Should be async method
    assert inspect.iscoroutinefunction(repo.soft_delete_comment)
    
    # Check required parameters exist
    assert "comment_id" in params
    assert "author_id" in params


def test_methods_raise_not_implemented():
    """Test that non-implemented methods raise NotImplementedError as expected during init phase."""
    repo = CommentRepository(db=MagicMock())

    # Test list_comments_by_thread raises NotImplementedError
    async def test_list():
        try:
            await repo.list_comments_by_thread(thread_id="thr_test")
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError:
            pass

    # Test soft_delete_comment raises NotImplementedError  
    async def test_delete():
        try:
            await repo.soft_delete_comment(
                comment_id="cmt_test",
                author_id="usr_test"
            )
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError:
            pass

    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_list())
        loop.run_until_complete(test_delete())
    finally:
        loop.close()


def test_create_comment_success():
    """Test successful comment creation."""
    # Mock DB responses
    mock_db = AsyncMock()
    mock_db.fetchrow = AsyncMock(return_value={
        "id": "cmt_01HX123456789ABCDEFGHJKMNP",
        "created_at": datetime(2025, 8, 9, 7, 0, 0, tzinfo=timezone.utc)
    })
    mock_db.execute = AsyncMock()
    
    repo = CommentRepository(db=mock_db)
    
    async def run_test():
        result = await repo.create_comment(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            body="Test comment body"
        )
        
        # Should return the comment ID
        assert result == "cmt_01HX123456789ABCDEFGHJKMNP"
        
        # Should call fetchrow for INSERT with RETURNING
        mock_db.fetchrow.assert_called_once()
        insert_query = mock_db.fetchrow.call_args[0][0]
        assert "INSERT INTO comments" in insert_query
        assert "RETURNING" in insert_query
        
        # Should call execute for UPDATE threads
        mock_db.execute.assert_called_once()
        update_query = mock_db.execute.call_args[0][0]
        assert "UPDATE threads" in update_query
        assert "last_activity_at" in update_query
    
    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()


def test_create_comment_with_image():
    """Test comment creation with image key."""
    mock_db = AsyncMock()
    mock_db.fetchrow = AsyncMock(return_value={
        "id": "cmt_01HX123456789ABCDEFGHJKMNP", 
        "created_at": datetime(2025, 8, 9, 7, 0, 0, tzinfo=timezone.utc)
    })
    mock_db.execute = AsyncMock()
    
    repo = CommentRepository(db=mock_db)
    
    async def run_test():
        result = await repo.create_comment(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            thread_id="thr_01HX123456789ABCDEFGHJKMNP", 
            body="Comment with image",
            image_key="uploads/2025/08/test.jpg"
        )
        
        assert result == "cmt_01HX123456789ABCDEFGHJKMNP"
        mock_db.fetchrow.assert_called_once()
        mock_db.execute.assert_called_once()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()


def test_create_comment_foreign_key_error():
    """Test comment creation with non-existent thread_id."""
    import asyncpg
    
    # Mock foreign key constraint violation
    mock_db = AsyncMock()
    mock_db.fetchrow = AsyncMock(side_effect=asyncpg.ForeignKeyViolationError("foreign key violation"))
    
    repo = CommentRepository(db=mock_db)
    
    async def run_test():
        try:
            await repo.create_comment(
                author_id="usr_01HX123456789ABCDEFGHJKMNP",
                thread_id="thr_nonexistent",
                body="Test comment"
            )
            assert False, "Should have raised ForeignKeyViolationError"
        except asyncpg.ForeignKeyViolationError:
            pass  # Expected
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_test())
    finally:
        loop.close()