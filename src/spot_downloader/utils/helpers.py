import shutil
import os


def get_ffmpeg_path():
    """
    Returns the path to FFmpeg executable.
    Checks system PATH first, then falls back to bundled imageio-ffmpeg.
    Returns None if FFmpeg is not available.
    """
    # Check system PATH first (user-installed FFmpeg)
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # Fall back to bundled imageio-ffmpeg
    try:
        import imageio_ffmpeg
        bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled_ffmpeg and os.path.exists(bundled_ffmpeg):
            return bundled_ffmpeg
    except ImportError:
        pass
    except Exception:
        pass

    return None


def check_ffmpeg():
    """
    Checks if FFmpeg is available (either system-installed or bundled).
    Required by yt-dlp for audio conversion.
    """
    return get_ffmpeg_path() is not None
