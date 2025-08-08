"""
カーソルユーティリティのテスト
"""
import json
import base64
from datetime import datetime, timedelta


def test_encode_decode_roundtrip():
    """エンコード/デコードの往復で同一オブジェクトになることを確認"""
    from app.services.cursor import encode, decode
    
    test_data = {
        "v": 1,
        "anchor": {
            "createdAt": "2024-01-01T00:00:00Z",
            "id": "thr_01ARYZ6S41TSV4RRFFQ69G5FAV"
        },
        "snapshotAt": "2024-01-01T00:00:00Z"
    }
    
    # エンコード
    cursor = encode(test_data)
    assert isinstance(cursor, str)
    assert len(cursor) > 0
    
    # デコード
    decoded = decode(cursor)
    assert decoded == test_data
    
    # base64urlエンコーディングの確認（パディングなし）
    assert not cursor.endswith('=')
    assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in cursor)


def test_validate_threads_cursor():
    """スレッドカーソルの検証が正しく動作することを確認"""
    from app.services.cursor import validate_threads_cursor
    
    # 有効なカーソル
    valid_cursor = {
        "v": 1,
        "anchor": {
            "createdAt": "2024-01-01T00:00:00Z",
            "id": "thr_01ARYZ6S41TSV4RRFFQ69G5FAV",
            "score": 100  # hotカーソル用
        },
        "snapshotAt": "2024-01-01T00:00:00Z"
    }
    
    anchor, errors = validate_threads_cursor(valid_cursor)
    assert anchor is not None
    assert errors is None
    assert anchor["createdAt"] == "2024-01-01T00:00:00Z"
    assert anchor["id"] == "thr_01ARYZ6S41TSV4RRFFQ69G5FAV"
    assert anchor["score"] == 100
    
    # 必須フィールドが欠けているカーソル
    invalid_cursor = {
        "v": 1,
        "anchor": {
            "id": "thr_01ARYZ6S41TSV4RRFFQ69G5FAV"
            # createdAtが欠けている
        },
        "snapshotAt": "2024-01-01T00:00:00Z"
    }
    
    anchor, errors = validate_threads_cursor(invalid_cursor)
    assert anchor is None
    assert errors is not None
    assert "createdAt" in str(errors)
    
    # 追加プロパティは許可される
    cursor_with_extra = {
        "v": 1,
        "anchor": {
            "createdAt": "2024-01-01T00:00:00Z",
            "id": "thr_01ARYZ6S41TSV4RRFFQ69G5FAV",
            "extraField": "allowed"
        },
        "snapshotAt": "2024-01-01T00:00:00Z",
        "extraTop": "also allowed"
    }
    
    anchor, errors = validate_threads_cursor(cursor_with_extra)
    assert anchor is not None
    assert errors is None


def test_validate_comments_cursor():
    """コメントカーソルの検証が正しく動作することを確認"""
    from app.services.cursor import validate_comments_cursor
    
    # 有効なカーソル
    valid_cursor = {
        "v": 1,
        "anchor": {
            "createdAt": "2024-01-01T00:00:00Z",
            "id": "cmt_01ARYZ6S41TSV4RRFFQ69G5FAV"
        }
    }
    
    anchor, errors = validate_comments_cursor(valid_cursor)
    assert anchor is not None
    assert errors is None
    assert anchor["createdAt"] == "2024-01-01T00:00:00Z"
    assert anchor["id"] == "cmt_01ARYZ6S41TSV4RRFFQ69G5FAV"
    
    # 無効なIDプレフィックス
    invalid_cursor = {
        "v": 1,
        "anchor": {
            "createdAt": "2024-01-01T00:00:00Z",
            "id": "thr_01ARYZ6S41TSV4RRFFQ69G5FAV"  # cmtではなくthr
        }
    }
    
    anchor, errors = validate_comments_cursor(invalid_cursor)
    assert anchor is None
    assert errors is not None


def test_is_snapshot_expired():
    """スナップショット期限チェックが正しく動作することを確認"""
    from app.services.cursor import is_snapshot_expired
    
    now = datetime.utcnow()
    
    # 23時間前（期限内）
    recent_snapshot = now - timedelta(hours=23)
    assert not is_snapshot_expired(recent_snapshot, now)
    
    # 25時間前（期限切れ）
    old_snapshot = now - timedelta(hours=25)
    assert is_snapshot_expired(old_snapshot, now)
    
    # ちょうど24時間前（境界値）
    boundary_snapshot = now - timedelta(hours=24)
    assert not is_snapshot_expired(boundary_snapshot, now)
    
    # 24時間と1秒前（期限切れ）
    expired_snapshot = now - timedelta(hours=24, seconds=1)
    assert is_snapshot_expired(expired_snapshot, now)


def test_decode_invalid_cursor():
    """無効なカーソルのデコードでエラーが発生することを確認"""
    from app.services.cursor import decode
    
    # 無効なbase64
    try:
        decode("not-valid-base64!")
        assert False, "Should raise exception for invalid base64"
    except Exception as e:
        assert "Invalid cursor" in str(e) or "decode" in str(e).lower()
    
    # 有効なbase64だがJSONではない
    not_json = base64.urlsafe_b64encode(b"not json").decode('ascii').rstrip('=')
    try:
        decode(not_json)
        assert False, "Should raise exception for non-JSON content"
    except Exception as e:
        assert "Invalid" in str(e) or "JSON" in str(e)


def test_encode_with_special_characters():
    """特殊文字を含むデータのエンコード/デコードが正しく動作することを確認"""
    from app.services.cursor import encode, decode
    
    test_data = {
        "v": 1,
        "anchor": {
            "createdAt": "2024-01-01T00:00:00Z",
            "id": "thr_01ARYZ6S41TSV4RRFFQ69G5FAV",
            "title": "日本語タイトル🎉"
        },
        "snapshotAt": "2024-01-01T00:00:00Z"
    }
    
    cursor = encode(test_data)
    decoded = decode(cursor)
    assert decoded == test_data
    assert decoded["anchor"]["title"] == "日本語タイトル🎉"