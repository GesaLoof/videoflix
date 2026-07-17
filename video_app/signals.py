import shutil
import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from .models import Video
from .tasks import transcode_video


@receiver(post_save, sender=Video)
def trigger_transcoding(sender, instance, created, **kwargs):
    """Queue an ffmpeg transcoding job when a new video is uploaded."""
    if created and instance.upload:
        transcode_video.delay(instance.id, instance.upload.path)


@receiver(post_save, sender=Video)
def clear_video_cache(sender, instance, **kwargs):
    """Invalidate the cached video list whenever a video is saved or updated."""
    cache.delete('video_list')


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """
    Remove the raw upload, thumbnail and HLS folder from disk when a video
    is deleted, preventing orphaned files from accumulating in the media volume.
    """
    if instance.upload:
        if os.path.isfile(instance.upload.path):
            os.remove(instance.upload.path)

    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)

    hls_dir = os.path.join(settings.HLS_ROOT, str(instance.id))
    if os.path.isdir(hls_dir):
        shutil.rmtree(hls_dir)


@receiver(post_delete, sender=Video)
def clear_cache_on_delete(sender, instance, **kwargs):
    """Invalidate the cached video list when a video is deleted."""
    cache.delete('video_list')