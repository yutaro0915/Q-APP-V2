from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Tuple


# base64url（パディング無し）

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    # パディングを補う
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def encode(obj: dict) -> str:
    """辞書をJSON→base64url（no padding）でエンコードする。"""
    raw = json.dumps(obj, separators=(",", ":"))
    return _b64url_encode(raw.encode("utf-8"))


def decode(cursor: str) -> dict:
    """base64url（no padding）→JSONの辞書へデコードする。"""
    raw = _b64url_decode(cursor)
    return json.loads(raw.decode("utf-8"))


def is_snapshot_expired(snapshot_at: datetime, now: datetime) -> bool:
    """スナップショットが24h超で期限切れ。境界24hは許容。"""
    # 念のためUTCに正規化
    if snapshot_at.tzinfo is None:
        snapshot_at = snapshot_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - snapshot_at) > timedelta(hours=24)


# 以下は将来のアンカー検証向けのプレースホルダ（本Issueでは未使用）
@dataclass(frozen=True)
class Anchor:
    created_at: datetime | None = None
    id: str | None = None


def validate_comments_cursor(obj: dict) -> Tuple[Anchor | None, list[dict[str, Any]] | None]:
    # v=1 のみを許容し、最低限のキー存在だけ確認する想定（詳細は後続Issueで実装）
    if not isinstance(obj, dict) or obj.get("v") != 1:
        return None, [{"field": "cursor.v", "reason": "INVALID"}]
    return Anchor(), None


def validate_threads_cursor(obj: dict) -> Tuple[Anchor | None, list[dict[str, Any]] | None]:
    if not isinstance(obj, dict) or obj.get("v") != 1:
        return None, [{"field": "cursor.v", "reason": "INVALID"}]
    return Anchor(), None