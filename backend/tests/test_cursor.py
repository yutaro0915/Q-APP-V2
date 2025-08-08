from datetime import datetime, timedelta, timezone
import re

from app.services.cursor import (
    encode,
    decode,
    validate_comments_cursor,
    validate_threads_cursor,
    is_snapshot_expired,
)


def test_encode_decode_roundtrip_and_paddingless():
    obj = {
        "v": 1,
        "sort": "new",
        "anchor": {"createdAt": "2025-08-06T09:00:00Z", "id": "thr_00000000000000000000000000"},
    }
    token = encode(obj)
    assert "=" not in token
    back = decode(token)
    assert back == obj


def test_is_snapshot_expired_24h_window():
    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=25)
    recent = now - timedelta(hours=23)
    assert is_snapshot_expired(old, now) is True
    assert is_snapshot_expired(recent, now) is False


def test_validate_comments_cursor_ok_and_ng():
    ok = {"v": 1, "anchor": {"createdAt": "2025-08-06T01:02:03Z", "id": "cmt_00000000000000000000000000"}}
    anchor, errors = validate_comments_cursor(ok)
    assert errors is None and anchor is not None

    ng = {"v": 1, "anchor": {"createdAt": "invalid", "id": "bad"}}
    anchor2, errors2 = validate_comments_cursor(ng)
    assert anchor2 is None and errors2 is not None


def test_validate_threads_cursor_new_and_hot():
    # new
    cur_new = {
        "v": 1,
        "sort": "new",
        "anchor": {"createdAt": "2025-08-06T03:04:05Z", "id": "thr_00000000000000000000000000"},
    }
    a1, e1 = validate_threads_cursor(cur_new)
    assert e1 is None and a1 is not None

    # hot
    cur_hot = {
        "v": 1,
        "sort": "hot",
        "snapshotAt": "2025-08-06T09:00:00Z",
        "anchor": {
            "score": 12.34,
            "createdAt": "2025-08-06T03:04:05Z",
            "id": "thr_00000000000000000000000000",
        },
    }
    a2, e2 = validate_threads_cursor(cur_hot)
    assert e2 is None and a2 is not None

    # hot NG (missing snapshotAt)
    cur_hot_ng = {
        "v": 1,
        "sort": "hot",
        "anchor": {"score": 1.0, "createdAt": "2025-08-06T03:04:05Z", "id": "thr_00000000000000000000000000"},
    }
    a3, e3 = validate_threads_cursor(cur_hot_ng)
    assert a3 is None and e3 is not None

import base64
import json
from datetime import datetime, timedelta, timezone

from app.services.cursor import encode, decode, is_snapshot_expired


def test_encode_decode_roundtrip():
    obj = {"v": 1, "a": {"createdAt": "2025-01-01T00:00:00Z", "id": "thr_00000000000000000000000000"}}
    cur = encode(obj)
    back = decode(cur)
    assert back == obj


def test_is_snapshot_expired_24h_rule():
    now = datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    snapshot = now - timedelta(hours=24, minutes=1)
    assert is_snapshot_expired(snapshot, now) is True

    snapshot_ok = now - timedelta(hours=23, minutes=59)
    assert is_snapshot_expired(snapshot_ok, now) is False