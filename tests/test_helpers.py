import os
import sys
# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import check_ffmpeg

def test_check_ffmpeg():
    # This just checks if the function runs without error
    # Result depends on system state
    result = check_ffmpeg()
    assert isinstance(result, bool)
