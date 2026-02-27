"""
Tests for helper utilities.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from spot_downloader.utils.helpers import get_ffmpeg_path, check_ffmpeg
from spot_downloader.utils.retry import retry
from spot_downloader.utils.throttle import Throttler


class TestFfmpegHelpers:
    """Test FFmpeg helper functions."""

    def test_get_ffmpeg_path_returns_string_or_none(self):
        """Test get_ffmpeg_path returns string or None."""
        result = get_ffmpeg_path()
        assert result is None or isinstance(result, str)

    def test_check_ffmpeg_returns_bool(self):
        """Test check_ffmpeg returns boolean."""
        result = check_ffmpeg()
        assert isinstance(result, bool)


class TestThrottler:
    """Test Throttler utility."""

    def test_throttler_init(self):
        """Test Throttler initializes with interval."""
        throttler = Throttler(0.1)
        assert throttler.interval == 0.1
        assert throttler.last_call == 0

    def test_throttler_calls_function(self):
        """Test Throttler calls function after interval."""
        throttler = Throttler(0.01)
        result = []
        
        def callback(value):
            result.append(value)
        
        throttler(callback, 1)
        throttler(callback, 2)  # Should be throttled
        import time
        time.sleep(0.02)
        throttler(callback, 3)
        
        assert len(result) >= 2


class TestRetryDecorator:
    """Test retry decorator."""

    def test_retry_succeeds_on_first_try(self):
        """Test retry succeeds on first attempt."""
        @retry(max_attempts=3, delay=0.01)
        def succeed():
            return "success"
        
        assert succeed() == "success"

    def test_retry_eventually_succeeds(self):
        """Test retry succeeds after failures."""
        attempts = [0]
        
        @retry(max_attempts=3, delay=0.01)
        def fail_then_succeed():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        assert fail_then_succeed() == "success"
        assert attempts[0] == 2

    def test_retry_exhausts_attempts(self):
        """Test retry raises exception after max attempts."""
        @retry(max_attempts=3, delay=0.01)
        def always_fail():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fail()
