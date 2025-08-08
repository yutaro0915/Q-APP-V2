"""Cursor encoding/decoding utilities for pagination."""

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple


class CursorDecodeError(Exception):
    """Error raised when cursor decoding fails."""
    pass


def encode(obj: Dict[str, Any]) -> str:
    """Encode a dictionary to base64url cursor string.
    
    Args:
        obj: Dictionary to encode
    
    Returns:
        Base64url encoded string without padding
    """
    json_str = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    # Encode to base64url without padding
    b64 = base64.urlsafe_b64encode(json_bytes).decode('ascii')
    # Remove padding
    return b64.rstrip('=')


def decode(cursor: str) -> Dict[str, Any]:
    """Decode a base64url cursor string to dictionary.
    
    Args:
        cursor: Base64url encoded cursor string
    
    Returns:
        Decoded dictionary
    
    Raises:
        CursorDecodeError: If cursor is invalid
    """
    try:
        # Add padding if needed
        padding = 4 - (len(cursor) % 4)
        if padding != 4:
            cursor += '=' * padding
        
        json_bytes = base64.urlsafe_b64decode(cursor)
        json_str = json_bytes.decode('utf-8')
        return json.loads(json_str)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise CursorDecodeError(f"Invalid cursor: {str(e)}")


def validate_comments_cursor(obj: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Validate a comments cursor object.
    
    Args:
        obj: Cursor object to validate
    
    Returns:
        Tuple of (anchor dict, error message)
        If valid, returns (anchor, None)
        If invalid, returns (None, error_message)
    """
    # Check version
    if obj.get("v") != 1:
        return None, "Invalid or missing cursor version"
    
    # Check required fields for comments (ASC order)
    if "createdAt" not in obj:
        return None, "Missing createdAt field"
    
    if "id" not in obj:
        return None, "Missing id field"
    
    # Validate date format
    try:
        datetime.fromisoformat(obj["createdAt"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None, "Invalid createdAt format"
    
    # Return anchor for pagination
    anchor = {
        "createdAt": obj["createdAt"],
        "id": obj["id"]
    }
    
    return anchor, None


def validate_threads_cursor(obj: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Validate a threads cursor object.
    
    Args:
        obj: Cursor object to validate
    
    Returns:
        Tuple of (anchor dict, error message)
        If valid, returns (anchor, None)
        If invalid, returns (None, error_message)
    """
    # Check version
    if obj.get("v") != 1:
        return None, "Invalid or missing cursor version"
    
    # Check required fields
    if "createdAt" not in obj:
        return None, "Missing createdAt field"
    
    if "id" not in obj:
        return None, "Missing id field"
    
    # Validate date format
    try:
        datetime.fromisoformat(obj["createdAt"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None, "Invalid createdAt format"
    
    # Build anchor based on sort type
    anchor = {
        "createdAt": obj["createdAt"],
        "id": obj["id"]
    }
    
    # If score is present (hot sort), validate and include it
    if "score" in obj:
        if not isinstance(obj["score"], (int, float)):
            return None, "Invalid score type"
        anchor["score"] = obj["score"]
    
    # If snapshot is present, include it
    if "snapshotAt" in obj:
        try:
            datetime.fromisoformat(obj["snapshotAt"].replace("Z", "+00:00"))
            anchor["snapshotAt"] = obj["snapshotAt"]
        except (ValueError, AttributeError):
            return None, "Invalid snapshotAt format"
    
    return anchor, None


def is_snapshot_expired(snapshot_at: datetime, now: datetime) -> bool:
    """Check if a snapshot timestamp has expired (>24 hours old).
    
    Args:
        snapshot_at: Snapshot timestamp
        now: Current timestamp
    
    Returns:
        True if expired, False otherwise
    """
    # Ensure both are timezone-aware
    if snapshot_at.tzinfo is None:
        snapshot_at = snapshot_at.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    
    age = now - snapshot_at
    return age >= timedelta(hours=24)