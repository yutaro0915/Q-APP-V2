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