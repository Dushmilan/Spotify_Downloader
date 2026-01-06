import shutil

def check_ffmpeg():
    """
    Checks if ffmpeg is installed on the system.
    spotdl requires ffmpeg to function correctly.
    """
    return shutil.which("ffmpeg") is not None
