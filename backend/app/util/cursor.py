"""Cursor utilities for pagination."""

import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class CursorDecodeError(Exception):
    """Error raised when cursor decoding fails."""
    pass


def encode_cursor(obj: Dict[str, Any]) -> str:
    """Encode a dictionary to base64url cursor.
    
    Args:
        obj: Dictionary to encode
        
    Returns:
        Base64url encoded string without padding
    """
    json_str = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    b64 = base64.urlsafe_b64encode(json_bytes).decode('ascii')
    # Remove padding
    return b64.rstrip('=')


def decode_cursor(cursor: str) -> Dict[str, Any]:
    """Decode base64url cursor to dictionary.
    
    Args:
        cursor: Base64url encoded cursor
        
    Returns:
        Decoded dictionary
        
    Raises:
        CursorDecodeError: If decoding fails
    """
    try:
        # Add padding if needed
        padding = 4 - (len(cursor) % 4)
        if padding != 4:
            cursor += '=' * padding
        
        json_bytes = base64.urlsafe_b64decode(cursor)
        json_str = json_bytes.decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        raise CursorDecodeError(f"Failed to decode cursor: {e}")


def validate_threads_cursor(obj: Dict[str, Any]) -> tuple:
    """Validate thread cursor format.
    
    Args:
        obj: Decoded cursor dictionary
        
    Returns:
        Tuple of (anchor dict, errors dict) where anchor is valid cursor data
        or (None, errors) if invalid
    """
    errors = {}
    
    # Check version if present (v is optional, defaults to 1)
    if "v" in obj and obj.get("v") != 1:
        errors["v"] = "Version must be 1"
    
    # Check required fields for thread cursor
    required_fields = ["createdAt", "id"]
    for field in required_fields:
        if field not in obj:
            errors[field] = f"{field} is required"
    
    # If there are errors, return None for anchor
    if errors:
        return None, errors
    
    # Return anchor data
    anchor = {
        "createdAt": obj["createdAt"],
        "id": obj["id"]
    }
    
    # Include score if present (for hot cursor)
    if "score" in obj:
        anchor["score"] = obj["score"]
    
    return anchor, None


def validate_comments_cursor(obj: Dict[str, Any]) -> tuple:
    """Validate comment cursor format.
    
    Args:
        obj: Decoded cursor dictionary
        
    Returns:
        Tuple of (anchor dict, errors dict) where anchor is valid cursor data
        or (None, errors) if invalid
    """
    errors = {}
    
    # Check version if present (v is optional, defaults to 1)
    if "v" in obj and obj.get("v") != 1:
        errors["v"] = "Version must be 1"
    
    # Check required fields for comment cursor
    required_fields = ["createdAt", "id"]
    for field in required_fields:
        if field not in obj:
            errors[field] = f"{field} is required"
    
    # If there are errors, return None for anchor
    if errors:
        return None, errors
    
    # Return anchor data
    anchor = {
        "createdAt": obj["createdAt"],
        "id": obj["id"]
    }
    
    return anchor, None


def is_snapshot_expired(snapshot_at: datetime, now: Optional[datetime] = None) -> bool:
    """Check if snapshot is expired (older than 24 hours).
    
    Args:
        snapshot_at: Snapshot timestamp
        now: Current time (defaults to UTC now)
        
    Returns:
        True if expired, False otherwise
    """
    if now is None:
        now = datetime.now(timezone.utc)
    
    # Ensure both are timezone-aware
    if snapshot_at.tzinfo is None:
        snapshot_at = snapshot_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    
    # Check if 24 hours or more old
    delta = now - snapshot_at
    return delta.total_seconds() >= 24 * 60 * 60


# Compatibility aliases
encode = encode_cursor
decode = decode_cursor