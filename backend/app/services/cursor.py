from __future__ import annotations

import base64
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.util.idgen import ID_PATTERN


def _json_dumps_compact(obj: dict[str, Any]) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, sort_keys=True)


def encode(obj: dict[str, Any]) -> str:
    """base64url(JSON) エンコード。パディング無し。"""
    raw = _json_dumps_compact(obj).encode("utf-8")
    token = base64.urlsafe_b64encode(raw).decode("ascii")
    return token.rstrip("=")


def decode(cursor: str) -> dict[str, Any]:
    """base64url(JSON) デコード。パディング無し入力を許容。"""
    pad_len = (4 - (len(cursor) % 4)) % 4
    padded = cursor + ("=" * pad_len)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def _parse_iso8601_utc(value: str) -> datetime:
    # Z を +00:00 に正規化
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_snapshot_expired(snapshot_at: datetime, now: datetime) -> bool:
    return (now - snapshot_at) > timedelta(hours=24)


def _err(field: str, reason: str) -> dict[str, str]:
    return {"field": field, "reason": reason}


def _is_valid_id(expected_prefix: str, value: str) -> bool:
    return bool(re.fullmatch(ID_PATTERN, value)) and value.startswith(expected_prefix + "_")


def validate_comments_cursor(obj: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]] | None]:
    errors: list[dict[str, str]] = []
    if not isinstance(obj, dict):
        return None, [_err("cursor", "INVALID_TYPE")]

    anchor = obj.get("anchor")
    if not isinstance(anchor, dict):
        return None, [_err("anchor", "REQUIRED")]

    created_at = anchor.get("createdAt")
    _id = anchor.get("id")
    try:
        _ = _parse_iso8601_utc(created_at)
    except Exception:
        errors.append(_err("anchor.createdAt", "INVALID_ISO8601"))

    if not isinstance(_id, str) or not _is_valid_id("cmt", _id):
        errors.append(_err("anchor.id", "INVALID_ID"))

    return (anchor, None) if not errors else (None, errors)


def validate_threads_cursor(obj: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]] | None]:
    errors: list[dict[str, str]] = []
    if not isinstance(obj, dict):
        return None, [_err("cursor", "INVALID_TYPE")]

    sort = obj.get("sort")
    if sort not in ("new", "hot"):
        return None, [_err("sort", "INVALID_VALUE")]

    anchor = obj.get("anchor")
    if not isinstance(anchor, dict):
        return None, [_err("anchor", "REQUIRED")]

    # Common checks
    created_at = anchor.get("createdAt")
    _id = anchor.get("id")
    try:
        _ = _parse_iso8601_utc(created_at)
    except Exception:
        errors.append(_err("anchor.createdAt", "INVALID_ISO8601"))
    if not isinstance(_id, str) or not _is_valid_id("thr", _id):
        errors.append(_err("anchor.id", "INVALID_ID"))

    if sort == "new":
        return (anchor, None) if not errors else (None, errors)

    # hot
    snapshot_at = obj.get("snapshotAt")
    if not isinstance(snapshot_at, str):
        errors.append(_err("snapshotAt", "REQUIRED"))
    else:
        try:
            _ = _parse_iso8601_utc(snapshot_at)
        except Exception:
            errors.append(_err("snapshotAt", "INVALID_ISO8601"))

    score = anchor.get("score")
    if not (isinstance(score, int) or isinstance(score, float)):
        errors.append(_err("anchor.score", "INVALID_NUMBER"))

    return (anchor, None) if not errors else (None, errors)