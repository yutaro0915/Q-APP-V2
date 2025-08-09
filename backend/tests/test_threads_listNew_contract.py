"""Test contract between ThreadService and ThreadRepository for list_threads_new."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.threads_service import ThreadService
from app.schemas.threads import PaginatedThreadCards


@pytest.mark.asyncio
async def test_list_threads_new_uses_repo_items_and_nextCursor():
    """Test that service correctly uses items and nextCursor from repository."""
    # Mock database connection
    mock_db = MagicMock()
    
    # Create service instance
    service = ThreadService(mock_db)
    
    # Mock repository response with items and nextCursor
    mock_repo = AsyncMock()
    mock_repo.list_threads_new = AsyncMock(return_value={
        "items": [
            {
                "id": "thr_01HX123456789ABCDEFGHJKMNP",
                "author_id": "usr_01HX000000000000000000000",
                "title": "Test Thread 1",
                "body": "Test body 1",
                "up_count": 5,
                "save_count": 2,
                "heat": 0,
                "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "last_activity_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None,
                "solved_comment_id": None
            },
            {
                "id": "thr_01HX223456789ABCDEFGHJKMNP",
                "author_id": "usr_01HX111111111111111111111",
                "title": "Test Thread 2",
                "body": "Test body 2",
                "up_count": 3,
                "save_count": 1,
                "heat": 0,
                "created_at": datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
                "last_activity_at": datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None,
                "solved_comment_id": None
            }
        ],
        "nextCursor": "eyJ2IjoxLCJjcmVhdGVkQXQiOiIyMDI0LTAxLTAxVDExOjAwOjAwWiIsImlkIjoidGhyXzAxSFgyMjM0NTY3ODlBQkNERUZHSEpLTU5QIn0"
    })
    
    # Patch ThreadRepository to use our mock
    from unittest.mock import patch
    with patch("app.services.threads_service.ThreadRepository", return_value=mock_repo):
        # Call list_threads_new
        result = await service.list_threads_new(
            cursor=None,
            current_user_id="usr_01HX000000000000000000000"
        )
    
    # Verify the result
    assert isinstance(result, PaginatedThreadCards)
    assert len(result.items) == 2
    assert result.items[0].id == "thr_01HX123456789ABCDEFGHJKMNP"
    assert result.items[1].id == "thr_01HX223456789ABCDEFGHJKMNP"
    
    # Verify nextCursor is passed through from repository
    assert result.nextCursor == "eyJ2IjoxLCJjcmVhdGVkQXQiOiIyMDI0LTAxLTAxVDExOjAwOjAwWiIsImlkIjoidGhyXzAxSFgyMjM0NTY3ODlBQkNERUZHSEpLTU5QIn0"


@pytest.mark.asyncio
async def test_list_threads_new_handles_no_nextCursor():
    """Test that service handles when repository returns no nextCursor."""
    # Mock database connection
    mock_db = MagicMock()
    
    # Create service instance
    service = ThreadService(mock_db)
    
    # Mock repository response with items but no nextCursor
    mock_repo = AsyncMock()
    mock_repo.list_threads_new = AsyncMock(return_value={
        "items": [
            {
                "id": "thr_01HX123456789ABCDEFGHJKMNP",
                "author_id": "usr_01HX000000000000000000000",
                "title": "Test Thread",
                "body": "Test body",
                "up_count": 0,
                "save_count": 0,
                "heat": 0,
                "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "last_activity_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "deleted_at": None,
                "solved_comment_id": None
            }
        ],
        "nextCursor": None
    })
    
    # Patch ThreadRepository to use our mock
    from unittest.mock import patch
    with patch("app.services.threads_service.ThreadRepository", return_value=mock_repo):
        # Call list_threads_new
        result = await service.list_threads_new(
            cursor=None,
            current_user_id="usr_01HX000000000000000000000"
        )
    
    # Verify the result
    assert isinstance(result, PaginatedThreadCards)
    assert len(result.items) == 1
    assert result.nextCursor is None


@pytest.mark.asyncio
async def test_list_threads_new_handles_empty_items():
    """Test that service handles when repository returns empty items list."""
    # Mock database connection
    mock_db = MagicMock()
    
    # Create service instance
    service = ThreadService(mock_db)
    
    # Mock repository response with empty items
    mock_repo = AsyncMock()
    mock_repo.list_threads_new = AsyncMock(return_value={
        "items": [],
        "nextCursor": None
    })
    
    # Patch ThreadRepository to use our mock
    from unittest.mock import patch
    with patch("app.services.threads_service.ThreadRepository", return_value=mock_repo):
        # Call list_threads_new
        result = await service.list_threads_new(
            cursor=None,
            current_user_id="usr_01HX000000000000000000000"
        )
    
    # Verify the result
    assert isinstance(result, PaginatedThreadCards)
    assert len(result.items) == 0
    assert result.nextCursor is None