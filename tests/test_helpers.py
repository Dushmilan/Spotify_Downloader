import os
import sys
# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from spot_downloader.utils.helpers import check_ffmpeg

def test_check_ffmpeg():
    # This just checks if the function runs without error
    # Result depends on system state
    result = check_ffmpeg()
    assert isinstance(result, bool)
