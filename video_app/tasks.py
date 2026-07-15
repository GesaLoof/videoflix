import django_rq
from .transcoder import transcode_to_hls
from .models import Video


@django_rq.job
def transcode_video(video_id, input_path):
    """Transcode a video to HLS and update its processing status."""

    video = Video.objects.get(pk=video_id)
    try:
        transcode_to_hls(video_id, input_path)
        video.hls_ready = True
    except Exception as e:
        print(f"Transcoding failed for video {video_id}: {e}")
        video.hls_ready = False
        raise e
    finally:
        video.save()
