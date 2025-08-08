"""
ULID ID生成ユーティリティのテスト
"""
import re
from typing import Set


def test_generate_id_formats():
    """各prefixで正しい形式のIDが生成されることを確認"""
    from app.util.idgen import generate_id
    
    prefixes = ['usr', 'cre', 'ses', 'thr', 'cmt', 'att', 'rcn']
    
    for prefix in prefixes:
        id_val = generate_id(prefix)
        assert id_val.startswith(f"{prefix}_"), f"ID should start with {prefix}_"
        assert len(id_val) == len(prefix) + 1 + 26, f"ID length should be {len(prefix) + 27}"
        
        # ULID部分の文字が正しいか確認（Base32）
        ulid_part = id_val.split('_')[1]
        assert len(ulid_part) == 26, "ULID part should be 26 characters"
        # Base32の文字セット（Crockford's Base32）
        assert re.match(r'^[0-9A-HJKMNP-TV-Z]{26}$', ulid_part), "ULID should use Crockford's Base32"


def test_id_pattern_constant():
    """ID_PATTERN定数が正しく定義されていることを確認"""
    from app.util.idgen import ID_PATTERN
    
    # 正規表現として有効か確認
    pattern = re.compile(ID_PATTERN)
    
    # 有効なIDがマッチすることを確認
    valid_ids = [
        "usr_01ARYZ6S41TSV4RRFFQ69G5FAV",
        "ses_01ARYZ6S41TSV4RRFFQ69G5FAV",
        "thr_01ARYZ6S41TSV4RRFFQ69G5FAV",
        "cmt_01ARYZ6S41TSV4RRFFQ69G5FAV",
        "att_01ARYZ6S41TSV4RRFFQ69G5FAV",
        "rcn_01ARYZ6S41TSV4RRFFQ69G5FAV",
        "cre_01ARYZ6S41TSV4RRFFQ69G5FAV",
    ]
    
    for valid_id in valid_ids:
        assert pattern.match(valid_id), f"{valid_id} should match ID_PATTERN"
    
    # 無効なIDがマッチしないことを確認
    invalid_ids = [
        "usr01ARYZ6S41TSV4RRFFQ69G5FAV",  # アンダースコアなし
        "usr_01ARYZ6S41TSV4RRFFQ69G5FA",   # 短い
        "usr_01ARYZ6S41TSV4RRFFQ69G5FAVX", # 長い
        "xxx_01ARYZ6S41TSV4RRFFQ69G5FAV",  # 無効なprefix
        "usr_01ARYZ6S41TSV4RRFFQ69G5FAI",  # Iは無効（Base32にない）
        "usr_01ARYZ6S41TSV4RRFFQ69G5FAO",  # Oは無効（Base32にない）
    ]
    
    for invalid_id in invalid_ids:
        assert not pattern.match(invalid_id), f"{invalid_id} should not match ID_PATTERN"


def test_id_uniqueness():
    """生成されるIDがユニークであることを確認"""
    from app.util.idgen import generate_id
    
    # 同じprefixで複数のIDを生成
    ids: Set[str] = set()
    prefix = 'usr'
    
    for _ in range(100):
        new_id = generate_id(prefix)
        assert new_id not in ids, f"Duplicate ID generated: {new_id}"
        ids.add(new_id)
    
    assert len(ids) == 100, "All generated IDs should be unique"


def test_generated_id_matches_pattern():
    """生成されたIDがID_PATTERNにマッチすることを確認"""
    from app.util.idgen import generate_id, ID_PATTERN
    
    pattern = re.compile(ID_PATTERN)
    prefixes = ['usr', 'cre', 'ses', 'thr', 'cmt', 'att', 'rcn']
    
    for prefix in prefixes:
        id_val = generate_id(prefix)
        assert pattern.match(id_val), f"Generated ID {id_val} should match ID_PATTERN"