"""ID generation utilities using ULID."""

import re
from typing import Literal
from ulid import ULID

# Valid prefixes for different entity types
PrefixType = Literal['usr', 'cre', 'ses', 'thr', 'cmt', 'att', 'rcn']

# Regular expression pattern for validating IDs
# Format: prefix_ULID where ULID is 26 characters of Crockford's Base32
ID_PATTERN = r'^(usr|cre|ses|thr|cmt|att|rcn)_[0-9A-HJKMNP-TV-Z]{26}$'


def generate_id(prefix: PrefixType) -> str:
    """Generate a prefixed ULID.
    
    Args:
        prefix: Entity type prefix (usr, cre, ses, thr, cmt, att, rcn)
    
    Returns:
        String in format "{prefix}_{ULID}" where ULID is 26 characters
    
    Raises:
        ValueError: If prefix is not valid
    """
    valid_prefixes = {'usr', 'cre', 'ses', 'thr', 'cmt', 'att', 'rcn'}
    
    if prefix not in valid_prefixes:
        raise ValueError(f"Invalid prefix: {prefix}. Must be one of {valid_prefixes}")
    
    # Generate ULID and convert to string
    ulid = str(ULID())
    
    return f"{prefix}_{ulid}"


def is_valid_id(id_str: str) -> bool:
    """Validate an ID string against the expected format.
    
    Args:
        id_str: ID string to validate
    
    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(ID_PATTERN, id_str))