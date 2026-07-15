from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Video
from .tasks import transcode_video

@receiver(post_save, sender=Video)
def trigger_transcoding(sender, instance, created, **kwargs):
    if created and instance.upload:
        transcode_video.delay(instance.id, instance.upload.path)