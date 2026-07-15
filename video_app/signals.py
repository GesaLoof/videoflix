from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Video
from .tasks import transcode_video
from django.core.cache import cache

@receiver(post_save, sender=Video)
def trigger_transcoding(sender, instance, created, **kwargs):
    if created and instance.upload:
        transcode_video.delay(instance.id, instance.upload.path)

@receiver(post_save, sender=Video)
def clear_video_cache(sender, instance, **kwargs):
    cache.delete('video_list')