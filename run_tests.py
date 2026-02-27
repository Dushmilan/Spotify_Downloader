"""
Test runner for the Spotify Downloader project.
"""

import pytest
import sys
import os

if __name__ == "__main__":
    print("=" * 60)
    print("Spotify Downloader - Test Suite")
    print("=" * 60)
    print()

    # Run pytest on the tests directory
    args = [
        "tests",
        "-v",
        "--tb=short",
        "--cov=src/spot_downloader",
        "--cov-report=term-missing",
    ]

    exit_code = pytest.main(args)

    print()
    print("=" * 60)
    if exit_code == 0:
        print("[SUCCESS] All tests passed!")
    else:
        print(f"[WARN] Some tests failed (Exit code: {exit_code})")
    print("=" * 60)

    sys.exit(exit_code)
