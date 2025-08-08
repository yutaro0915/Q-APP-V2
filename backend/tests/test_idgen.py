import re
from app.util.idgen import generate_id, ID_PATTERN


def test_generate_id_format_and_regex():
    prefixes = ["usr", "cre", "ses", "thr", "cmt", "att", "rcn"]
    pattern = re.compile(ID_PATTERN)

    seen = set()
    for prefix in prefixes:
        # 生成
        value = generate_id(prefix)  # e.g. usr_01HZY...

        # 形式検証
        assert value.startswith(prefix + "_")
        assert len(value) == len(prefix) + 1 + 26

        # 正規表現検証
        assert pattern.fullmatch(value) is not None

        # 一意性（弱検証）
        seen.add(value)

    # すべてユニーク
    assert len(seen) == len(prefixes)