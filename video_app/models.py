from django.db import models


class Category(models.Model):
    """Video category."""

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Video(models.Model):
    """Video uploaded for streaming."""

    title = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True)
    upload = models.FileField(upload_to="uploads/", null=False)
    thumbnail = models.ImageField(upload_to="thumbnails/", null=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    hls_ready = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
