import django_rq
from .transcoder import transcode_to_hls
from .models import Video


@django_rq.job
def transcode_video(video_id, input_path):    
    """
    RQ background job that transcodes a video to HLS format at multiple resolutions.
    Sets hls_ready to True on success or False on failure, always saving the result.
    Decorated with @django_rq.job so it can be queued with transcode_video.delay().
    """

    video = Video.objects.get(pk=video_id)
    try:
        transcode_to_hls(video_id, input_path)
        video.hls_ready = True
    except Exception:
        print(f"Transcoding failed for video {video_id}")
        video.hls_ready = False
        raise
    finally:
        video.save()
