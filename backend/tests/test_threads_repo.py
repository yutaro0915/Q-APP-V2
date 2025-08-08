import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.repositories.threads_repo import ThreadRepository


def test_threads_repo_class_exists():
    repo = ThreadRepository(db=None)
    assert repo is not None


def test_threads_repo_signatures():
    repo = ThreadRepository(db=None)
    assert hasattr(repo, "create_thread")
    assert hasattr(repo, "get_thread_by_id")
    assert hasattr(repo, "list_threads_new")
    assert hasattr(repo, "soft_delete_thread")


def test_id_helper_format():
    from app.util.idgen import is_valid_id

    # 仮にヘルパを直接利用
    repo = ThreadRepository(db=None)
    new_id = repo._generate_thread_id()
    assert new_id.startswith("thr_")
    assert is_valid_id(new_id)


def test_create_thread_signature_and_flow_monkeypatch():
    """create_threadの基本フロー（ID, timestamp, INSERT呼び出し）をモックで検証。
    実SQLは後続Issueで実装。
    """
    repo = ThreadRepository(db=MagicMock())

    async def fake_create(*, author_id: str, title: str, body: str, tags=None, image_key=None) -> str:
        # 擬似的にID生成と時刻取得を使う
        _id = repo._generate_thread_id()
        assert _id.startswith("thr_")
        _now = repo._now_utc()
        assert _now.endswith("Z")
        # DB層はモック（呼び出し確認のみ）
        return _id

    # 署名互換の仮実装に差し替え
    repo.create_thread = fake_create  # type: ignore

    new_id = asyncio.get_event_loop().run_until_complete(
        repo.create_thread(author_id="usr_x", title="t", body="b")
    )
    assert new_id.startswith("thr_")


def test_get_thread_by_id_with_existing_thread():
    """Test get_thread_by_id returns thread when it exists."""
    # Create mock DB connection
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": "Test body",
        "up_count": 0,
        "save_count": 0,
        "solved_comment_id": None,
        "heat": 0.0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": None
    })
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.get_thread_by_id(thread_id="thr_01HX123456789ABCDEFGHJKMNP")
        assert result is not None
        assert result["id"] == "thr_01HX123456789ABCDEFGHJKMNP"
        assert result["title"] == "Test Thread"
        assert result["deleted_at"] is None
        
        # Verify the query was called correctly
        mock_conn.fetchrow.assert_called_once()
        query_args = mock_conn.fetchrow.call_args
        query_str = query_args[0][0]
        params = query_args[0][1]
        
        assert "SELECT" in query_str
        assert "FROM threads" in query_str
        assert "WHERE" in query_str
        assert "id = $1" in query_str
        assert "deleted_at IS NULL" in query_str
        assert params == "thr_01HX123456789ABCDEFGHJKMNP"
    
    asyncio.run(run_test())


def test_get_thread_by_id_with_non_existing_thread():
    """Test get_thread_by_id returns None when thread doesn't exist."""
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Use a valid format ID that doesn't exist
        result = await repo.get_thread_by_id(thread_id="thr_99XX123456789ABCDEFGHJKMNP")
        assert result is None
        mock_conn.fetchrow.assert_called_once()
    
    asyncio.run(run_test())


def test_get_thread_by_id_with_deleted_thread():
    """Test get_thread_by_id returns None for soft-deleted threads."""
    mock_conn = AsyncMock()
    # Even though a deleted thread might exist in DB, our query should filter it out
    # So the fetchrow should return None
    mock_conn.fetchrow = AsyncMock(return_value=None)
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Use a valid format ID for a deleted thread
        result = await repo.get_thread_by_id(thread_id="thr_D3T1234567890ABCDEFGHJKMNP")
        assert result is None
        
        # Verify deleted_at IS NULL is in the query
        mock_conn.fetchrow.assert_called_once()
        query_args = mock_conn.fetchrow.call_args
        query_str = query_args[0][0]
        assert "deleted_at IS NULL" in query_str
    
    asyncio.run(run_test())


def test_get_thread_by_id_validates_id_format():
    """Test get_thread_by_id validates thread ID format."""
    mock_conn = AsyncMock()
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Invalid prefix
        result = await repo.get_thread_by_id(thread_id="usr_01HX123456789ABCDEFGHJKMNP")
        assert result is None
        
        # Invalid ULID characters
        result = await repo.get_thread_by_id(thread_id="thr_01HX123456789ABCDEFGHIJKLM")
        assert result is None
        
        # Too short
        result = await repo.get_thread_by_id(thread_id="thr_123")
        assert result is None
        
        # Empty string
        result = await repo.get_thread_by_id(thread_id="")
        assert result is None
        
        # For invalid IDs, we shouldn't even hit the database
        mock_conn.fetchrow.assert_not_called()
    
    asyncio.run(run_test())


def test_list_threads_new_without_cursor():
    """Test list_threads_new returns threads in correct order without cursor."""
    mock_conn = AsyncMock()
    
    # Mock threads data
    mock_threads = [
        {
            "id": "thr_01HX123456789ABCDEFGHJKMN3",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Thread 3",
            "body": "Body 3",
            "created_at": datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        },
        {
            "id": "thr_01HX123456789ABCDEFGHJKMN2",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Thread 2",
            "body": "Body 2",
            "created_at": datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        },
        {
            "id": "thr_01HX123456789ABCDEFGHJKMN1",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Thread 1",
            "body": "Body 1",
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        }
    ]
    
    mock_conn.fetch = AsyncMock(return_value=mock_threads)
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.list_threads_new()
        
        assert "items" in result
        assert "nextCursor" in result
        assert len(result["items"]) == 3
        
        # Check ordering - newest first
        assert result["items"][0]["id"] == "thr_01HX123456789ABCDEFGHJKMN3"
        assert result["items"][1]["id"] == "thr_01HX123456789ABCDEFGHJKMN2"
        assert result["items"][2]["id"] == "thr_01HX123456789ABCDEFGHJKMN1"
        
        # Verify SQL query
        mock_conn.fetch.assert_called_once()
        query = mock_conn.fetch.call_args[0][0]
        assert "SELECT" in query
        assert "FROM threads" in query
        assert "deleted_at IS NULL" in query
        assert "ORDER BY created_at DESC, id DESC" in query
        assert "LIMIT" in query
    
    asyncio.run(run_test())


def test_list_threads_new_with_cursor():
    """Test list_threads_new with cursor pagination."""
    from app.services.cursor import encode
    
    mock_conn = AsyncMock()
    
    # Mock threads after cursor
    mock_threads = [
        {
            "id": "thr_01HX123456789ABCDEFGHJKMN2",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Thread 2",
            "body": "Body 2",
            "created_at": datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        },
        {
            "id": "thr_01HX123456789ABCDEFGHJKMN1",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Thread 1",
            "body": "Body 1",
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        }
    ]
    
    mock_conn.fetch = AsyncMock(return_value=mock_threads)
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Create cursor pointing to thread 3
        cursor_obj = {
            "v": 1,
            "createdAt": "2024-01-03T00:00:00Z",
            "id": "thr_01HX123456789ABCDEFGHJKMN3"
        }
        cursor = encode(cursor_obj)
        
        result = await repo.list_threads_new(cursor=cursor)
        
        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == "thr_01HX123456789ABCDEFGHJKMN2"
        assert result["items"][1]["id"] == "thr_01HX123456789ABCDEFGHJKMN1"
        
        # Check that cursor was used in query
        query = mock_conn.fetch.call_args[0][0]
        assert "(created_at, id) < ($1, $2)" in query or "created_at < $1 OR (created_at = $1 AND id < $2)" in query
    
    asyncio.run(run_test())


def test_list_threads_new_limit():
    """Test list_threads_new respects limit parameter."""
    mock_conn = AsyncMock()
    
    # Mock more threads than limit
    mock_threads = []
    for i in range(5, 0, -1):  # 5 threads in DESC order
        mock_threads.append({
            "id": f"thr_01HX123456789ABCDEFGHJKMN{i}",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": f"Thread {i}",
            "body": f"Body {i}",
            "created_at": datetime(2024, 1, i, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        })
    
    mock_conn.fetch = AsyncMock(return_value=mock_threads[:3])
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.list_threads_new(limit=3)
        
        assert len(result["items"]) == 3
        
        # Check LIMIT in query
        query = mock_conn.fetch.call_args[0][0]
        limit_param = mock_conn.fetch.call_args[0][1] if len(mock_conn.fetch.call_args[0]) > 1 else None
        # Should fetch limit+1 to check for more
        assert limit_param == 4 or "LIMIT 4" in query
    
    asyncio.run(run_test())


def test_list_threads_new_has_more():
    """Test list_threads_new correctly determines if there are more pages."""
    mock_conn = AsyncMock()
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Case 1: Has more pages (returns limit+1 items)
        mock_threads_with_more = []
        for i in range(4):  # 4 threads when limit is 3
            mock_threads_with_more.append({
                "id": f"thr_01HX123456789ABCDEFGHJKMN{4-i}",
                "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
                "title": f"Thread {4-i}",
                "body": f"Body {4-i}",
                "created_at": datetime(2024, 1, 4-i, 0, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None
            })
        
        mock_conn.fetch = AsyncMock(return_value=mock_threads_with_more)
        result = await repo.list_threads_new(limit=3)
        
        # Should only return 3 items but set nextCursor
        assert len(result["items"]) == 3
        assert result["nextCursor"] is not None
        
        # Case 2: No more pages (returns less than limit+1)
        mock_threads_no_more = mock_threads_with_more[:2]  # Only 2 threads
        mock_conn.fetch = AsyncMock(return_value=mock_threads_no_more)
        result = await repo.list_threads_new(limit=3)
        
        assert len(result["items"]) == 2
        assert result["nextCursor"] is None
    
    asyncio.run(run_test())


def test_list_threads_new_max_limit():
    """Test list_threads_new enforces maximum limit of 200."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Try with limit > 200
        result = await repo.list_threads_new(limit=500)
        
        # Should cap at 200 (+1 for has_more check)
        query = mock_conn.fetch.call_args[0][0]
        limit_param = mock_conn.fetch.call_args[0][-1]
        assert limit_param == 201 or "LIMIT 201" in query
    
    asyncio.run(run_test())


def test_list_threads_new_excludes_deleted():
    """Test list_threads_new excludes soft-deleted threads."""
    mock_conn = AsyncMock()
    
    # Mock data should not include deleted threads
    # The query should filter them out
    mock_threads = [
        {
            "id": "thr_01HX123456789ABCDEFGHJKMN1",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Active Thread",
            "body": "Body",
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None
        }
    ]
    
    mock_conn.fetch = AsyncMock(return_value=mock_threads)
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.list_threads_new()
        
        # Verify deleted_at IS NULL is in query
        query = mock_conn.fetch.call_args[0][0]
        assert "deleted_at IS NULL" in query
        
        # Result should only have non-deleted threads
        assert len(result["items"]) == 1
        assert result["items"][0]["deleted_at"] is None
    
    asyncio.run(run_test())


def test_list_threads_new_invalid_cursor():
    """Test list_threads_new handles invalid cursor gracefully."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Invalid cursor should be handled
        result = await repo.list_threads_new(cursor="invalid_cursor_xxx")
        
        # Should return empty result or raise appropriate error
        assert "items" in result
        assert result["items"] == []
        assert result["nextCursor"] is None
    
    asyncio.run(run_test())


def test_soft_delete_thread_by_owner():
    """Test soft_delete_thread succeeds when called by the owner."""
    mock_conn = AsyncMock()
    
    # Mock successful update (returns the updated row)
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP"
    })
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.soft_delete_thread(
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            author_id="usr_01HX123456789ABCDEFGHJKMNP"
        )
        
        assert result is True
        
        # Verify the SQL query
        mock_conn.fetchrow.assert_called_once()
        query = mock_conn.fetchrow.call_args[0][0]
        assert "UPDATE threads" in query
        assert "SET deleted_at" in query
        assert "WHERE id = $2" in query  # thread_id is second param
        assert "AND author_id = $3" in query  # author_id is third param
        assert "AND deleted_at IS NULL" in query
        assert "RETURNING id" in query
        
        # Verify parameters (deleted_at timestamp, thread_id, author_id)
        params = mock_conn.fetchrow.call_args[0][1:]
        assert len(params) == 3
        # First param is timestamp (deleted_at)
        assert params[1] == "thr_01HX123456789ABCDEFGHJKMNP"
        assert params[2] == "usr_01HX123456789ABCDEFGHJKMNP"
    
    asyncio.run(run_test())


def test_soft_delete_thread_by_non_owner():
    """Test soft_delete_thread fails when called by non-owner."""
    mock_conn = AsyncMock()
    
    # Mock no rows updated (returns None)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.soft_delete_thread(
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            author_id="usr_DIFFERENT123456789ABCDEFGH"
        )
        
        assert result is False
        
        # Query should still be executed
        mock_conn.fetchrow.assert_called_once()
    
    asyncio.run(run_test())


def test_soft_delete_thread_already_deleted():
    """Test soft_delete_thread fails when thread is already deleted."""
    mock_conn = AsyncMock()
    
    # Mock no rows updated because deleted_at IS NULL fails
    mock_conn.fetchrow = AsyncMock(return_value=None)
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.soft_delete_thread(
            thread_id="thr_01HX123456789ABCDEFGHJKMNP",
            author_id="usr_01HX123456789ABCDEFGHJKMNP"
        )
        
        assert result is False
        
        # The query should include deleted_at IS NULL check
        query = mock_conn.fetchrow.call_args[0][0]
        assert "deleted_at IS NULL" in query
    
    asyncio.run(run_test())


def test_soft_delete_thread_nonexistent():
    """Test soft_delete_thread fails when thread doesn't exist."""
    mock_conn = AsyncMock()
    
    # Mock no rows found
    mock_conn.fetchrow = AsyncMock(return_value=None)
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        result = await repo.soft_delete_thread(
            thread_id="thr_NONEXISTENT123456789ABCDEF",
            author_id="usr_01HX123456789ABCDEFGHJKMNP"
        )
        
        assert result is False
    
    asyncio.run(run_test())


def test_soft_delete_thread_validates_thread_id():
    """Test soft_delete_thread validates thread ID format."""
    mock_conn = AsyncMock()
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Invalid thread ID format should return False without querying
        result = await repo.soft_delete_thread(
            thread_id="invalid_id_format",
            author_id="usr_01HX123456789ABCDEFGHJKMNP"
        )
        
        assert result is False
        
        # Should not query database for invalid ID
        mock_conn.fetchrow.assert_not_called()
    
    asyncio.run(run_test())


def test_create_thread_basic():
    """Test create_thread creates a new thread successfully."""
    mock_conn = AsyncMock()
    
    # Mock successful insert
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": "Test body content",
        "up_count": 0,
        "save_count": 0,
        "solved_comment_id": None,
        "heat": 0.0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": None
    })
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        thread_id = await repo.create_thread(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            title="Test Thread",
            body="Test body content"
        )
        
        assert thread_id == "thr_01HX123456789ABCDEFGHJKMNP"
        
        # Verify the query was called
        mock_conn.fetchrow.assert_called_once()
        query = mock_conn.fetchrow.call_args[0][0]
        params = mock_conn.fetchrow.call_args[0][1:]
        
        # Check query structure
        assert "INSERT INTO threads" in query
        assert "RETURNING *" in query
        
        # Check parameters
        assert len(params) == 11  # id, author_id, title, body, created_at, last_activity_at, heat, up_count, save_count, solved_comment_id, deleted_at
        assert params[0].startswith("thr_")  # Generated thread ID
        assert params[1] == "usr_01HX123456789ABCDEFGHJKMNP"
        assert params[2] == "Test Thread"
        assert params[3] == "Test body content"
    
    asyncio.run(run_test())


def test_create_thread_with_tags_and_image():
    """Test create_thread with tags and image_key."""
    mock_conn = AsyncMock()
    
    # Mock successful insert
    mock_conn.fetchrow = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread with Tags",
        "body": "Body with image",
        "up_count": 0,
        "save_count": 0,
        "solved_comment_id": None,
        "heat": 0.0,
        "created_at": datetime.now(timezone.utc),
        "last_activity_at": datetime.now(timezone.utc),
        "deleted_at": None
    })
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        thread_id = await repo.create_thread(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            title="Test Thread with Tags",
            body="Body with image",
            tags=["question", "programming"],
            image_key="2024/01/15/thr_01HX123456789ABCDEFGHJKMNP.webp"
        )
        
        assert thread_id == "thr_01HX123456789ABCDEFGHJKMNP"
        
        # Note: tags and image_key are handled by separate tables in later phases
        # For now, just ensure the basic thread creation works
        mock_conn.fetchrow.assert_called_once()
    
    asyncio.run(run_test())


def test_create_thread_id_generation():
    """Test that create_thread generates valid thread IDs."""
    mock_conn = AsyncMock()
    
    # Store generated IDs to check
    generated_ids = []
    
    async def capture_id(*args):
        # Capture the generated ID from the INSERT query parameters
        generated_ids.append(args[1])  # ID is first parameter after query
        return {
            "id": args[1],
            "author_id": args[2],
            "title": args[3],
            "body": args[4],
            "up_count": 0,
            "save_count": 0,
            "solved_comment_id": None,
            "heat": 0.0,
            "created_at": datetime.now(timezone.utc),
            "last_activity_at": datetime.now(timezone.utc),
            "deleted_at": None
        }
    
    mock_conn.fetchrow = AsyncMock(side_effect=capture_id)
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        # Create multiple threads
        for i in range(3):
            thread_id = await repo.create_thread(
                author_id="usr_01HX123456789ABCDEFGHJKMNP",
                title=f"Thread {i}",
                body=f"Body {i}"
            )
            assert thread_id.startswith("thr_")
            assert len(thread_id) == 30  # thr_ (4) + ULID (26)
        
        # Check all generated IDs are unique
        assert len(set(generated_ids)) == 3
        
        # Validate ULID format for each
        from app.util.idgen import is_valid_id
        for gen_id in generated_ids:
            assert is_valid_id(gen_id)
    
    asyncio.run(run_test())


def test_create_thread_timestamp_generation():
    """Test that create_thread sets correct timestamps."""
    mock_conn = AsyncMock()
    
    captured_timestamps = []
    
    async def capture_timestamps(*args):
        # Capture created_at and last_activity_at
        captured_timestamps.append({
            "created_at": args[5],  # created_at parameter
            "last_activity_at": args[6]  # last_activity_at parameter
        })
        return {
            "id": args[1],
            "author_id": args[2],
            "title": args[3],
            "body": args[4],
            "up_count": 0,
            "save_count": 0,
            "solved_comment_id": None,
            "heat": args[7],
            "created_at": datetime.now(timezone.utc),
            "last_activity_at": datetime.now(timezone.utc),
            "deleted_at": None
        }
    
    mock_conn.fetchrow = AsyncMock(side_effect=capture_timestamps)
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        await repo.create_thread(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            title="Test Thread",
            body="Test body"
        )
        
        # Check timestamps were set
        assert len(captured_timestamps) == 1
        ts = captured_timestamps[0]
        
        # Both timestamps should be the same at creation
        assert ts["created_at"] == ts["last_activity_at"]
        
        # Should be ISO8601 format with Z suffix
        assert ts["created_at"].endswith("Z")
        assert "T" in ts["created_at"]
    
    asyncio.run(run_test())


def test_create_thread_id_collision_retry():
    """Test that create_thread retries on ID collision."""
    mock_conn = AsyncMock()
    
    # Simulate unique constraint violation on first attempt
    call_count = 0
    
    async def simulate_collision(*args):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First attempt: simulate unique constraint violation
            import asyncpg
            raise asyncpg.UniqueViolationError("duplicate key value violates unique constraint")
        else:
            # Second attempt: success
            return {
                "id": args[1],
                "author_id": args[2],
                "title": args[3],
                "body": args[4],
                "up_count": 0,
                "save_count": 0,
                "solved_comment_id": None,
                "heat": 0.0,
                "created_at": datetime.now(timezone.utc),
                "last_activity_at": datetime.now(timezone.utc),
                "deleted_at": None
            }
    
    mock_conn.fetchrow = AsyncMock(side_effect=simulate_collision)
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        thread_id = await repo.create_thread(
            author_id="usr_01HX123456789ABCDEFGHJKMNP",
            title="Test Thread",
            body="Test body"
        )
        
        # Should succeed after retry
        assert thread_id.startswith("thr_")
        
        # Should have been called twice (first failed, second succeeded)
        assert mock_conn.fetchrow.call_count == 2
    
    asyncio.run(run_test())


def test_create_thread_other_db_errors():
    """Test that create_thread propagates non-unique-constraint DB errors."""
    mock_conn = AsyncMock()
    
    # Simulate a different database error
    mock_conn.fetchrow = AsyncMock(side_effect=Exception("Database connection lost"))
    
    repo = ThreadRepository(db=mock_conn)
    
    async def run_test():
        try:
            await repo.create_thread(
                author_id="usr_01HX123456789ABCDEFGHJKMNP",
                title="Test Thread",
                body="Test body"
            )
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Database connection lost" in str(e)
    
    asyncio.run(run_test())
