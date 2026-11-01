"""
Simple in-memory rate limiter middleware for Flask.

Implements sliding window rate limiting to prevent abuse and ensure
application reliability under load.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict
from functools import wraps
from flask import request, jsonify


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    
    Tracks requests per IP address and enforces configurable limits.
    Suitable for single-instance deployments. For distributed systems,
    use Redis-backed rate limiting.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for given identifier.
        
        Args:
            identifier: Unique identifier (typically IP address)
            
        Returns:
            Tuple of (is_allowed: bool, remaining: int)
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        current_count = len(self.requests[identifier])
        if current_count < self.max_requests:
            self.requests[identifier].append(now)
            return True, self.max_requests - current_count - 1
        
        return False, 0
    
    def get_retry_after(self, identifier: str) -> int:
        """
        Get seconds until rate limit resets.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Seconds until oldest request expires
        """
        if not self.requests[identifier]:
            return 0
        
        oldest_request = min(self.requests[identifier])
        reset_time = oldest_request + timedelta(seconds=self.window_seconds)
        remaining = (reset_time - datetime.now()).total_seconds()
        return max(0, int(remaining))


# Global rate limiter instances
rate_limiter_default = RateLimiter(max_requests=100, window_seconds=60)
rate_limiter_strict = RateLimiter(max_requests=20, window_seconds=60)


def rate_limit(limiter: RateLimiter = None):
    """
    Decorator to apply rate limiting to Flask routes.
    
    Args:
        limiter: RateLimiter instance (uses default if None)
        
    Returns:
        Decorated function with rate limiting applied
        
    Example:
        @app.route("/api/endpoint")
        @rate_limit()
        def my_endpoint():
            return {"data": "value"}
    """
    if limiter is None:
        limiter = rate_limiter_default
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP address)
            identifier = request.remote_addr or "unknown"
            
            # Check rate limit
            allowed, remaining = limiter.is_allowed(identifier)
            
            if not allowed:
                retry_after = limiter.get_retry_after(identifier)
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(limiter.max_requests)
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Reset'] = str(
                    int((datetime.now() + timedelta(seconds=limiter.window_seconds)).timestamp())
                )
            
            return response
        
        return decorated_function
    return decorator
