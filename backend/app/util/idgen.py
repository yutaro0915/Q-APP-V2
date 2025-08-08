"""
ID生成ユーティリティ

Kyudai Campus SNS用のprefix付きULID生成機能を提供します。
形式: {prefix}_{ULID26}

例:
    usr_01ARYZ6S41TSV4RRFFQ69G5FAV
    thr_01ARYZ6S41TSV4RRFFQ69G5FAV
"""
import time
import os
import random
from typing import Literal

# Crockford's Base32 alphabet (excluding I, L, O, U)
BASE32_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# 正規表現パターン（バリデーション用）
ID_PATTERN = r"^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$"

# 有効なプレフィックス
PrefixType = Literal['usr', 'cre', 'ses', 'thr', 'cmt', 'att', 'rcn']


def _encode_base32(value: int, length: int) -> str:
    """整数値をBase32エンコード"""
    if value == 0:
        return '0' * length
    
    result = []
    while value > 0:
        result.append(BASE32_ALPHABET[value % 32])
        value //= 32
    
    # 必要な長さまでパディング
    while len(result) < length:
        result.append('0')
    
    return ''.join(reversed(result))


def _generate_ulid() -> str:
    """
    ULID（Universally Unique Lexicographically Sortable Identifier）を生成
    
    ULIDの構造:
    - 最初の10文字: タイムスタンプ（48ビット）
    - 残りの16文字: ランダム（80ビット）
    """
    # タイムスタンプ部分（ミリ秒単位のUNIXタイム、48ビット）
    timestamp = int(time.time() * 1000)
    timestamp_encoded = _encode_base32(timestamp, 10)
    
    # ランダム部分（80ビット = 16文字）
    # 80ビットのランダム値を生成
    random_bytes = os.urandom(10)  # 10バイト = 80ビット
    random_value = int.from_bytes(random_bytes, byteorder='big')
    random_encoded = _encode_base32(random_value, 16)
    
    return timestamp_encoded + random_encoded


def generate_id(prefix: PrefixType) -> str:
    """
    prefix付きのULID形式IDを生成
    
    Args:
        prefix: ID種別を表すプレフィックス
            - usr: ユーザー
            - cre: クレデンシャル
            - ses: セッション
            - thr: スレッド
            - cmt: コメント
            - att: 添付ファイル
            - rcn: リアクション
    
    Returns:
        生成されたID（形式: {prefix}_{ULID26}）
    
    Example:
        >>> id = generate_id('usr')
        >>> print(id)
        usr_01ARYZ6S41TSV4RRFFQ69G5FAV
    """
    ulid = _generate_ulid()
    return f"{prefix}_{ulid}"