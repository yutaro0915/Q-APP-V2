"""Test for ID generation utilities."""

import re
import pytest
from app.util.idgen import generate_id, ID_PATTERN


def test_generate_id_with_valid_prefixes():
    """Test ID generation with valid prefixes."""
    prefixes = ['usr', 'cre', 'ses', 'thr', 'cmt', 'att', 'rcn']
    
    for prefix in prefixes:
        id_value = generate_id(prefix)
        assert id_value.startswith(f"{prefix}_")
        assert len(id_value) == len(prefix) + 1 + 26  # prefix + underscore + 26 chars ULID
        assert re.match(ID_PATTERN, id_value)


def test_generate_id_uniqueness():
    """Test that generated IDs are unique."""
    # Generate multiple IDs and check uniqueness
    ids = set()
    for _ in range(100):
        new_id = generate_id('thr')
        assert new_id not in ids
        ids.add(new_id)


def test_generate_id_format():
    """Test the exact format of generated IDs."""
    # ULID uses specific character set (Crockford's Base32)
    valid_chars = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
    
    id_value = generate_id('usr')
    prefix, ulid_part = id_value.split('_')
    
    assert prefix == 'usr'
    assert len(ulid_part) == 26
    
    # Check all characters are valid Base32
    for char in ulid_part:
        assert char in valid_chars


def test_id_pattern_regex():
    """Test the ID_PATTERN regex matches correct IDs."""
    # Valid IDs
    valid_ids = [
        'usr_01HGXQZW8KPQRSTVWXYZ012345',
        'thr_01HGXQZW8KPQRSTVWXYZ012345',
        'cmt_01HGXQZW8KPQRSTVWXYZ012345',
        'ses_01HGXQZW8KPQRSTVWXYZ012345',
        'att_01HGXQZW8KPQRSTVWXYZ012345',
        'rcn_01HGXQZW8KPQRSTVWXYZ012345',
        'cre_01HGXQZW8KPQRSTVWXYZ012345',
    ]
    
    for valid_id in valid_ids:
        assert re.match(ID_PATTERN, valid_id)
    
    # Invalid IDs
    invalid_ids = [
        'invalid_01HGXQZW8KPQRSTVWXYZ012345',  # wrong prefix
        'usr01HGXQZW8KPQRSTVWXYZ012345',       # missing underscore
        'usr_01HGXQZW8KPQRSTVWXYZ01234',       # too short
        'usr_01HGXQZW8KPQRSTVWXYZ0123456',     # too long
        'usr_01HGXQZW8KPQRSTVWXYZ01234L',      # invalid character (L)
        'usr_01HGXQZW8KPQRSTVWXYZ01234I',      # invalid character (I)
        'usr_01HGXQZW8KPQRSTVWXYZ01234O',      # invalid character (O)
        'usr_01HGXQZW8KPQRSTVWXYZ01234U',      # invalid character (U)
    ]
    
    for invalid_id in invalid_ids:
        assert not re.match(f"^{ID_PATTERN}$", invalid_id)


def test_generate_id_invalid_prefix():
    """Test that invalid prefix raises an error."""
    with pytest.raises((ValueError, TypeError)):
        generate_id('invalid')
    
    with pytest.raises((ValueError, TypeError)):
        generate_id('')
    
    with pytest.raises((ValueError, TypeError)):
        generate_id(None)