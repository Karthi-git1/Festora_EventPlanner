"""Unit tests for rate limiter middleware.

Tests the rate limiting functionality to ensure reliability and
protection against abuse.
"""

import pytest
from datetime import datetime, timedelta
from middleware.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_rate_limiter_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        identifier = "192.168.1.1"
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, remaining = limiter.is_allowed(identifier)
            assert allowed is True
            assert remaining == 4 - i
    
    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        identifier = "192.168.1.1"
        
        # First 3 requests should be allowed
        for _ in range(3):
            allowed, _ = limiter.is_allowed(identifier)
            assert allowed is True
        
        # 4th request should be blocked
        allowed, remaining = limiter.is_allowed(identifier)
        assert allowed is False
        assert remaining == 0
    
    def test_rate_limiter_different_identifiers(self):
        """Test that different identifiers have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # IP 1 uses 2 requests
        allowed1, _ = limiter.is_allowed("192.168.1.1")
        allowed2, _ = limiter.is_allowed("192.168.1.1")
        assert allowed1 is True
        assert allowed2 is True
        
        # IP 2 should still have full quota
        allowed3, remaining = limiter.is_allowed("192.168.1.2")
        assert allowed3 is True
        assert remaining == 1
    
    def test_rate_limiter_window_expiration(self):
        """Test that requests expire after window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)  # 1 second window
        identifier = "192.168.1.1"
        
        # Use up the limit
        limiter.is_allowed(identifier)
        limiter.is_allowed(identifier)
        
        # Should be blocked
        allowed, _ = limiter.is_allowed(identifier)
        assert allowed is False
        
        # Wait for window to expire
        import time
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed(identifier)
        assert allowed is True
    
    def test_get_retry_after(self):
        """Test retry_after calculation."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        identifier = "192.168.1.1"
        
        # Use the limit
        limiter.is_allowed(identifier)
        
        # Get retry_after
        retry_after = limiter.get_retry_after(identifier)
        assert 0 < retry_after <= 60
    
    def test_rate_limiter_empty_identifier_list(self):
        """Test retry_after with no requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        retry_after = limiter.get_retry_after("new-ip")
        assert retry_after == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
