"""Test that excerpt uses the standard 120 character length."""

import pytest
from app.services.threads_service import ThreadService
from app.schemas.threads import create_excerpt


def test_thread_card_uses_standard_excerpt_length():
    """Test that excerpt uses 120 characters as defined in schemas."""
    service = ThreadService(db=None)
    
    # Create a long text that exceeds 120 characters
    long_text = "This is a very long text that will definitely exceed one hundred and twenty characters when we keep adding more and more words to it. We need to make sure the excerpt is properly truncated at exactly 120 characters with an ellipsis."
    
    thread_data = {
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": long_text,
        "up_count": 0,
        "save_count": 0,
        "heat": 0,
        "created_at": "2024-01-01T12:00:00Z",
        "last_activity_at": "2024-01-01T12:00:00Z",
        "deleted_at": None,
        "solved_comment_id": None
    }
    
    # Create thread card
    thread_card = service._to_thread_card(
        thread_data=thread_data,
        current_user_id="usr_01HX123456789ABCDEFGHJKMNP",
        tags=[]
    )
    
    # The excerpt should be exactly 121 characters (120 + ellipsis)
    assert len(thread_card.excerpt) == 121  # 120 chars + "…"
    assert thread_card.excerpt.endswith("…")
    
    # It should match what the standard create_excerpt produces
    expected_excerpt = create_excerpt(long_text, 120)
    assert thread_card.excerpt == expected_excerpt


def test_thread_card_excerpt_handles_newlines():
    """Test that excerpt properly handles newlines."""
    service = ThreadService(db=None)
    
    # Text with newlines
    text_with_newlines = "First line\n\nSecond line\r\nThird line"
    
    thread_data = {
        "id": "thr_01HX123456789ABCDEFGHJKMNP",
        "author_id": "usr_01HX123456789ABCDEFGHJKMNP",
        "title": "Test Thread",
        "body": text_with_newlines,
        "up_count": 0,
        "save_count": 0,
        "heat": 0,
        "created_at": "2024-01-01T12:00:00Z",
        "last_activity_at": "2024-01-01T12:00:00Z",
        "deleted_at": None,
        "solved_comment_id": None
    }
    
    # Create thread card
    thread_card = service._to_thread_card(
        thread_data=thread_data,
        current_user_id="usr_01HX123456789ABCDEFGHJKMNP",
        tags=[]
    )
    
    # Should replace newlines with spaces and compress multiple spaces
    expected_excerpt = create_excerpt(text_with_newlines, 120)
    assert thread_card.excerpt == expected_excerpt
    assert thread_card.excerpt == "First line Second line Third line"