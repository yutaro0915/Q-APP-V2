"""Test that authorAffiliation is properly set to None in Phase 1."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.threads_service import ThreadService
from app.schemas.threads import ThreadCard


@pytest.mark.asyncio
async def test_thread_card_author_affiliation_is_none():
    """Test that authorAffiliation is None in Phase 1."""
    mock_repo = AsyncMock()
    
    # Mock repository to return a thread
    mock_repo.get_thread_by_id = AsyncMock(return_value={
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": "Test body content",
        "up_count": 0,
        "save_count": 0,
        "heat": 0,
        "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "last_activity_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "deleted_at": None,
        "solved_comment_id": None
    })
    
    mock_conn = AsyncMock()
    service = ThreadService(db=mock_conn)
    
    # Call _to_thread_card directly
    thread_card = service._to_thread_card(
        thread_data={
            "id": "thr_01HX123456789ABCDEFGHJKMNP",
            "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
            "title": "Test Thread",
            "body": "Test body content",
            "up_count": 0,
            "save_count": 0,
            "heat": 0,
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "last_activity_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None,
            "solved_comment_id": None
        },
        current_user_id="usr_01HX123456789ABCDEFGHJKMNP",
        tags=[]
    )
    
    # Verify authorAffiliation is None (Phase 1 - no JOIN implementation)
    assert thread_card.authorAffiliation is None