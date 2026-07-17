import subprocess
import os
from django.conf import settings

# Output profiles used for HLS transcoding
RESOLUTIONS = {
    "480p": {"size": "854x480", "bitrate": "800k"},
    "720p": {"size": "1280x720", "bitrate": "2800k"},
    "1080p": {"size": "1920x1080", "bitrate": "5000k"},
}


def transcode_to_hls(movie_id, input_path):
    """
    Run ffmpeg for each resolution in RESOLUTIONS, producing 10-second .ts segments
    and an index.m3u8 playlist per resolution under HLS_ROOT/<movie_id>/<resolution>/.
    Uses libx264 for video and aac for audio. Raises CalledProcessError if ffmpeg fails.
    """

    for resolution, params in RESOLUTIONS.items():
        output_dir = os.path.join(settings.HLS_ROOT, str(movie_id), resolution)
        os.makedirs(output_dir, exist_ok=True)

        subprocess.run(
            [
                "ffmpeg",
                "-i",
                input_path,
                "-vf",
                f"scale={params['size']}",
                "-c:v",
                "libx264",
                "-b:v",
                params["bitrate"],
                "-c:a",
                "aac",
                "-hls_time",
                "10",
                "-hls_playlist_type",
                "vod",
                "-hls_segment_filename",
                os.path.join(output_dir, "segment%03d.ts"),
                os.path.join(output_dir, "index.m3u8"),
            ],
            check=True,
        )
