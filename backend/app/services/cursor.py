"""
カーソルユーティリティ

base64url(JSON)形式のカーソルのエンコード/デコードと検証機能を提供します。
ページネーション用のカーソルを安全に処理するためのユーティリティです。

カーソル形式:
    base64url({
        "v": 1,
        "anchor": {
            "createdAt": "ISO8601",
            "id": "リソースID",
            "score": 数値 (hotカーソルの場合)
        },
        "snapshotAt": "ISO8601" (hotカーソルの場合)
    })
"""
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional


def encode(obj: dict) -> str:
    """
    辞書をbase64url形式のカーソル文字列にエンコード
    
    Args:
        obj: エンコード対象の辞書
    
    Returns:
        base64urlエンコードされたカーソル文字列（パディングなし）
    """
    json_str = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    # base64urlエンコード（パディングなし）
    b64 = base64.urlsafe_b64encode(json_bytes).decode('ascii')
    # パディングを削除
    return b64.rstrip('=')


def decode(cursor: str) -> dict:
    """
    base64url形式のカーソル文字列を辞書にデコード
    
    Args:
        cursor: base64urlエンコードされたカーソル文字列
    
    Returns:
        デコードされた辞書
    
    Raises:
        ValueError: 無効なカーソル形式の場合
    """
    try:
        # パディングを追加（必要に応じて）
        padding = 4 - (len(cursor) % 4)
        if padding and padding != 4:
            cursor += '=' * padding
        
        # base64urlデコード
        json_bytes = base64.urlsafe_b64decode(cursor)
        json_str = json_bytes.decode('utf-8')
        
        # JSONパース
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid cursor format: {e}")


def validate_threads_cursor(obj: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    スレッドカーソルの検証
    
    Args:
        obj: 検証対象のカーソル辞書
    
    Returns:
        (anchor辞書, エラーメッセージ) のタプル
        検証成功時: (anchor, None)
        検証失敗時: (None, エラーメッセージ)
    """
    # バージョンチェック
    if obj.get('v') != 1:
        return None, "Invalid cursor version"
    
    # anchorの存在チェック
    anchor = obj.get('anchor')
    if not anchor:
        return None, "Missing anchor field"
    
    # 必須フィールドのチェック
    if 'createdAt' not in anchor:
        return None, "Missing createdAt in anchor"
    if 'id' not in anchor:
        return None, "Missing id in anchor"
    
    # IDフォーマットのチェック（thrプレフィックス）
    if not anchor['id'].startswith('thr_'):
        return None, "Invalid thread ID format"
    
    # 追加プロパティは許可（v=1等）
    return anchor, None


def validate_comments_cursor(obj: dict) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    コメントカーソルの検証
    
    Args:
        obj: 検証対象のカーソル辞書
    
    Returns:
        (anchor辞書, エラーメッセージ) のタプル
        検証成功時: (anchor, None)
        検証失敗時: (None, エラーメッセージ)
    """
    # バージョンチェック
    if obj.get('v') != 1:
        return None, "Invalid cursor version"
    
    # anchorの存在チェック
    anchor = obj.get('anchor')
    if not anchor:
        return None, "Missing anchor field"
    
    # 必須フィールドのチェック
    if 'createdAt' not in anchor:
        return None, "Missing createdAt in anchor"
    if 'id' not in anchor:
        return None, "Missing id in anchor"
    
    # IDフォーマットのチェック（cmtプレフィックス）
    if not anchor['id'].startswith('cmt_'):
        return None, "Invalid comment ID format"
    
    # 追加プロパティは許可
    return anchor, None


def is_snapshot_expired(snapshot_at: datetime, now: datetime) -> bool:
    """
    スナップショットが期限切れ（24時間以上経過）かどうかをチェック
    
    Args:
        snapshot_at: スナップショット時刻
        now: 現在時刻
    
    Returns:
        期限切れの場合True、そうでない場合False
    """
    # 24時間の期限
    expiry_duration = timedelta(hours=24)
    elapsed = now - snapshot_at
    
    # 24時間を超えているかチェック
    return elapsed > expiry_duration