from __future__ import annotations

import os
import time
import secrets
from typing import Literal

# Crockford's Base32 alphabet (uppercase, without I, L, O, U)
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# ID 形式の正規表現
ID_PATTERN: str = r"^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$"


def _now_millis() -> int:
    """UTCのエポックミリ秒（int）。"""
    return int(time.time() * 1000)


def _encode_base32_26(value: int) -> str:
    """128bit整数を Base32（Crockford）26桁へエンコード（大端）。"""
    chars: list[str] = ["0"] * 26
    for i in range(25, -1, -1):
        chars[i] = _ALPHABET[value & 0x1F]
        value >>= 5
    # 残りは0のはず（上位2bitはゼロ埋め）
    return "".join(chars)


def _generate_ulid26(now_ms: int | None = None) -> str:
    """ULID (26 chars) を生成。
    48bit: 時刻（ms） / 80bit: ランダム。
    """
    if now_ms is None:
        now_ms = _now_millis()
    # 48bit の時刻
    time_part = now_ms & ((1 << 48) - 1)
    # 80bit のランダム
    random_part = secrets.randbits(80)
    ulid128 = (time_part << 80) | random_part
    return _encode_base32_26(ulid128)


AllowedPrefix = Literal["usr", "cre", "ses", "thr", "cmt", "att", "rcn"]


def generate_id(prefix: AllowedPrefix) -> str:
    """`{prefix}_{ULID26}` 形式のIDを生成する。"""
    ulid = _generate_ulid26()
    return f"{prefix}_{ulid}"