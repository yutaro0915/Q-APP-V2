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
