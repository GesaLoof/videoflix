from django.conf import settings
from .models import Video
import os

VALID_RESOLUTIONS = ["480p", "720p", "1080p"]

def get_video_or_404(movie_id):
    """Return the video if it exists and is HLS-ready, or None."""
    try:
        return Video.objects.get(pk=movie_id, hls_ready=True)
    except Video.DoesNotExist:
        return None


def is_valid_resolution(resolution):
    """Check whether the requested resolution is supported."""
    return resolution in VALID_RESOLUTIONS


def get_playlist_path(movie_id, resolution):
    """Build the absolute path to the .m3u8 playlist file."""
    return os.path.join(settings.HLS_ROOT, str(movie_id), resolution, "index.m3u8")


def read_playlist(playlist_path):
    """Read and return the playlist file contents, or None if the file does not exist."""
    if not os.path.exists(playlist_path):
        return None
    with open(playlist_path, "r") as f:
        return f.read()
    
def is_valid_segment(segment):
    """Check the segment name is a .ts file and contains no path traversal characters."""
    return segment.endswith(".ts") and "/" not in segment and ".." not in segment


def get_segment_path(movie_id, resolution, segment):
    """Build the absolute path to the .ts segment file."""
    return os.path.join(settings.HLS_ROOT, str(movie_id), resolution, segment)