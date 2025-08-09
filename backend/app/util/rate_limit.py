"""Rate limiting utilities."""

import time
from typing import Dict, Tuple, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse


def generate_rate_limit_key(user_id: str, ip: Optional[str] = None) -> str:
    """Generate composite key for rate limiting.
    
    Args:
        user_id: User ID
        ip: Client IP address (optional)
        
    Returns:
        Composite key in format "user_id:ip" or just "user_id" if no IP
    """
    if ip and ip.strip():
        return f"{user_id}:{ip}"
    return user_id


def get_client_ip(request: Request) -> str:
    """Extract client IP from request.
    
    Checks X-Forwarded-For header first (takes first IP if multiple),
    falls back to request.client.host.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header
    forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded_for:
        # Take the first IP if there are multiple (client's real IP)
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return ""


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, limit: int = 1, window_seconds: int = 60):
        """Initialize rate limiter.
        
        Args:
            limit: Number of requests allowed per window
            window_seconds: Time window in seconds
        """
        self.limit = limit
        self.window_seconds = window_seconds
        # Store: user_id -> list of timestamps
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, Optional[int]]:
        """Check if user has exceeded rate limit.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old entries and count recent requests
        user_requests = self.requests[user_id]
        user_requests = [ts for ts in user_requests if ts > window_start]
        self.requests[user_id] = user_requests
        
        if len(user_requests) >= self.limit:
            # Calculate when the oldest request will expire
            oldest_request = min(user_requests)
            retry_after = int(oldest_request + self.window_seconds - now) + 1
            return False, retry_after
        
        # Add current request
        user_requests.append(now)
        return True, None
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Number of remaining requests
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        user_requests = self.requests[user_id]
        recent_requests = [ts for ts in user_requests if ts > window_start]
        
        return max(0, self.limit - len(recent_requests))
    
    def get_reset_time(self, user_id: str) -> int:
        """Get reset time for user's rate limit.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Unix timestamp when rate limit resets
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        user_requests = self.requests[user_id]
        recent_requests = [ts for ts in user_requests if ts > window_start]
        
        if recent_requests:
            oldest_request = min(recent_requests)
            return int(oldest_request + self.window_seconds)
        
        return int(now + self.window_seconds)
    
    def reset(self):
        """Reset all rate limit state (for testing)."""
        self.requests.clear()


# Global rate limiter instance for thread creation
# 1 thread per minute per user
rate_limiter = RateLimiter(limit=1, window_seconds=60)


def create_rate_limit_response(retry_after: int, limit: int, remaining: int, reset_time: int) -> JSONResponse:
    """Create standardized rate limit error response.
    
    Args:
        retry_after: Seconds until next request allowed
        limit: Rate limit per window
        remaining: Remaining requests in window
        reset_time: Unix timestamp when limit resets
        
    Returns:
        JSONResponse with error details and headers
    """
    response = JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMITED",
                "message": "Too many requests. Please wait before creating another thread.",
                "details": {
                    "retryAfter": retry_after,
                    "limit": limit,
                    "remaining": remaining,
                    "reset": reset_time
                }
            }
        }
    )
    
    # Add rate limit headers as per spec
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    return response