from .helpers import check_ffmpeg
from .tagger import tag_mp3, tag_m4a
from .validation import (
    validate_spotify_url,
    sanitize_filename,
    validate_download_path,
    is_safe_url
)
from .error_handling import (
    DownloadError,
    DownloadErrorType,
    setup_logging,
    log_error,
    handle_download_error
)
# from .spotify_bulk_operations import (
#     SpotifyBulkOperations,
#     get_all_playlist_tracks,
#     get_all_album_tracks
# )