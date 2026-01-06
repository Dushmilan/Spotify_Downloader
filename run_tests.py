import pytest
import sys
import os

if __name__ == "__main__":
    print("🚀 Starting Spot-Downloader Desktop Test Suite...\n")
    
    # Run pytest on the tests directory
    args = [
        "tests",
        "-v",
        "--tb=short"
    ]
    
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Some tests failed (Exit code: {exit_code})")
    
    sys.exit(exit_code)
