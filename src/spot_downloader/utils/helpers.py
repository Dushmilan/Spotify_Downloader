import shutil

def check_ffmpeg():
    """
    checks if ffmpeg is installed on the system.
    Required for yt-dlp to merge audio/video or convert formats.
    """
    return shutil.which("ffmpeg") is not None
