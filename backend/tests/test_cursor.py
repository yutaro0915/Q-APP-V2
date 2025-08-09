"""Test for cursor utilities."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.util.cursor import (
    encode,
    decode,
    validate_comments_cursor,
    validate_threads_cursor,
    is_snapshot_expired,
    CursorDecodeError,
)


def test_encode_decode_roundtrip():
    """Test that encode/decode produces the same object."""
    test_cases = [
        {"v": 1, "createdAt": "2024-01-01T00:00:00Z", "id": "thr_01HGXQZW8KPQRSTVWXYZ012345"},
        {"v": 1, "score": 100, "createdAt": "2024-01-01T00:00:00Z", "id": "thr_123"},
        {"v": 1, "extra": "field", "createdAt": "2024-01-01T00:00:00Z"},
    ]
    
    for obj in test_cases:
        cursor = encode(obj)
        decoded = decode(cursor)
        assert decoded == obj


def test_encode_produces_base64url():
    """Test that encode produces valid base64url without padding."""
    obj = {"v": 1, "test": "data"}
    cursor = encode(obj)
    
    # base64url should not contain +, /, or =
    assert "+" not in cursor
    assert "/" not in cursor
    assert "=" not in cursor
    
    # Should only contain base64url characters
    import string
    valid_chars = string.ascii_letters + string.digits + "-_"
    assert all(c in valid_chars for c in cursor)


def test_decode_invalid_cursor():
    """Test that decode raises error for invalid cursor."""
    invalid_cursors = [
        "not-base64",
        "!!!invalid!!!",
        "",
        "dGVzdA",  # valid base64 but not JSON
    ]
    
    for cursor in invalid_cursors:
        with pytest.raises(CursorDecodeError):
            decode(cursor)


def test_validate_comments_cursor_valid():
    """Test validation of valid comments cursor."""
    valid_cursor = {
        "v": 1,
        "createdAt": "2024-01-01T00:00:00Z",
        "id": "cmt_01HGXQZW8KPQRSTVWXYZ012345"
    }
    
    anchor, errors = validate_comments_cursor(valid_cursor)
    assert anchor is not None
    assert errors is None
    assert anchor["createdAt"] == "2024-01-01T00:00:00Z"
    assert anchor["id"] == "cmt_01HGXQZW8KPQRSTVWXYZ012345"


def test_validate_comments_cursor_invalid():
    """Test validation of invalid comments cursor."""
    invalid_cursors = [
        {},  # missing v
        {"v": 2},  # wrong version
        {"v": 1},  # missing fields
        {"v": 1, "createdAt": "invalid-date", "id": "cmt_123"},  # invalid date
        {"v": 1, "createdAt": "2024-01-01T00:00:00Z"},  # missing id
    ]
    
    for cursor in invalid_cursors:
        anchor, errors = validate_comments_cursor(cursor)
        assert anchor is None
        assert errors is not None


def test_validate_threads_cursor_valid():
    """Test validation of valid threads cursor."""
    # New threads cursor
    new_cursor = {
        "v": 1,
        "createdAt": "2024-01-01T00:00:00Z",
        "id": "thr_01HGXQZW8KPQRSTVWXYZ012345"
    }
    
    anchor, errors = validate_threads_cursor(new_cursor)
    assert anchor is not None
    assert errors is None
    
    # Hot threads cursor with snapshot
    hot_cursor = {
        "v": 1,
        "score": 100,
        "createdAt": "2024-01-01T00:00:00Z", 
        "id": "thr_01HGXQZW8KPQRSTVWXYZ012345",
        "snapshotAt": "2024-01-01T00:00:00Z"
    }
    
    anchor, errors = validate_threads_cursor(hot_cursor)
    assert anchor is not None
    assert errors is None
    assert anchor["score"] == 100


def test_validate_threads_cursor_invalid():
    """Test validation of invalid threads cursor."""
    invalid_cursors = [
        {"v": 1, "score": "not-a-number", "createdAt": "2024-01-01T00:00:00Z", "id": "thr_123"},
        {"v": 1, "createdAt": "2024-01-01T00:00:00Z"},  # missing id
        {"v": 1, "score": 100},  # missing createdAt and id for hot
    ]
    
    for cursor in invalid_cursors:
        anchor, errors = validate_threads_cursor(cursor)
        assert anchor is None
        assert errors is not None


def test_is_snapshot_expired():
    """Test snapshot expiration check."""
    now = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    
    # Not expired (23 hours old)
    snapshot_23h = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert not is_snapshot_expired(snapshot_23h, now)
    
    # Expired (25 hours old)
    snapshot_25h = datetime(2023, 12, 31, 23, 0, 0, tzinfo=timezone.utc)
    assert is_snapshot_expired(snapshot_25h, now)
    
    # Exactly 24 hours (should be expired)
    snapshot_24h = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert is_snapshot_expired(snapshot_24h, now)


def test_is_snapshot_expired_with_string():
    """Test snapshot expiration with ISO string input."""
    now = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    
    # String format
    snapshot_str = "2024-01-01T01:00:00Z"
    snapshot_dt = datetime.fromisoformat(snapshot_str.replace("Z", "+00:00"))
    assert not is_snapshot_expired(snapshot_dt, now)