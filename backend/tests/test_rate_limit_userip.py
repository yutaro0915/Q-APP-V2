"""Test rate limit with user+IP composite key."""

import pytest
from app.util.rate_limit import generate_rate_limit_key, get_client_ip
from fastapi import Request


def test_generate_rate_limit_key():
    """Test composite key generation for rate limiting."""
    # Test with both user_id and IP
    key = generate_rate_limit_key("usr_01234567890123456789012345", "192.168.1.1")
    assert key == "usr_01234567890123456789012345:192.168.1.1"
    
    # Test with just user_id (fallback)
    key = generate_rate_limit_key("usr_01234567890123456789012345", None)
    assert key == "usr_01234567890123456789012345"
    
    # Test with empty IP
    key = generate_rate_limit_key("usr_01234567890123456789012345", "")
    assert key == "usr_01234567890123456789012345"


def test_get_client_ip():
    """Test IP extraction from request."""
    # Test with X-Forwarded-For header (multiple IPs)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "headers": [(b"x-forwarded-for", b"203.0.113.1, 10.0.0.1, 172.16.0.1")],
            "client": ("127.0.0.1", 8000)
        }
    )
    ip = get_client_ip(request)
    assert ip == "203.0.113.1"  # Should return first IP
    
    # Test with single X-Forwarded-For
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "headers": [(b"x-forwarded-for", b"203.0.113.1")],
            "client": ("127.0.0.1", 8000)
        }
    )
    ip = get_client_ip(request)
    assert ip == "203.0.113.1"
    
    # Test without X-Forwarded-For (fallback to client.host)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "headers": [],
            "client": ("192.168.1.100", 8000)
        }
    )
    ip = get_client_ip(request)
    assert ip == "192.168.1.100"
    
    # Test with empty X-Forwarded-For
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "headers": [(b"x-forwarded-for", b"")],
            "client": ("192.168.1.100", 8000)
        }
    )
    ip = get_client_ip(request)
    assert ip == "192.168.1.100"  # Should fallback to client.host