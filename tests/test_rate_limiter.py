"""
Tests for rate limiting utilities.
"""

import os
import sys
import pytest
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.utils.rate_limiter import RateLimiter, rate_limit


class TestRateLimiter:
    """Test RateLimiter class."""

    def test_rate_limiter_allows_within_limit(self):
        """Test rate limiter allows calls within limit."""
        limiter = RateLimiter(calls=5, period=1)
        
        # Should allow 5 calls immediately
        for _ in range(5):
            assert limiter.acquire() is True

    def test_rate_limiter_blocks_over_limit(self):
        """Test rate limiter blocks calls over limit."""
        limiter = RateLimiter(calls=2, period=0.5)
        
        # Use up tokens
        limiter.acquire()
        limiter.acquire()
        
        # Next call should wait
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited for token replenishment
        assert elapsed > 0.1

    def test_rate_limiter_decorator(self):
        """Test rate limit decorator."""
        call_count = [0]
        
        @rate_limit(calls=3, period=1)
        def increment():
            call_count[0] += 1
            return call_count[0]
        
        # Should work within limit
        assert increment() == 1
        assert increment() == 2
        assert increment() == 3

    def test_rate_limiter_replenishes(self):
        """Test tokens replenish over time."""
        limiter = RateLimiter(calls=2, period=0.2)
        
        # Use up tokens
        limiter.acquire()
        limiter.acquire()
        
        # Wait for replenishment
        time.sleep(0.25)
        
        # Should have tokens again
        assert limiter.acquire() is True

