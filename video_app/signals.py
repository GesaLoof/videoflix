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
    if created and instance.upload:
        transcode_video.delay(instance.id, instance.upload.path)


@receiver(post_save, sender=Video)
def clear_video_cache(sender, instance, **kwargs):
    cache.delete('video_list')


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    print("DELETE SIGNAL FIRED for video:", instance.id)  # ← debug

    # delete raw upload
    if instance.upload:
        if os.path.isfile(instance.upload.path):
            os.remove(instance.upload.path)
            print("Deleted upload:", instance.upload.path)

    # delete thumbnail
    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)
            print("Deleted thumbnail:", instance.thumbnail.path)

    # delete HLS folder
    hls_dir = os.path.join(settings.HLS_ROOT, str(instance.id))
    if os.path.isdir(hls_dir):
        shutil.rmtree(hls_dir)
        print("Deleted HLS folder:", hls_dir)


@receiver(post_delete, sender=Video)
def clear_cache_on_delete(sender, instance, **kwargs):
    cache.delete('video_list')