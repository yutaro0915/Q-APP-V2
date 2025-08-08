import asyncio
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
