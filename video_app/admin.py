# videos/admin.py
from django.contrib import admin
from .models import Video, Category
from .tasks import transcode_video

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'hls_ready', 'created_at']
    readonly_fields = ['hls_ready', 'created_at']

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        print("IS NEW:", is_new)
        print("HAS UPLOAD:", obj.upload)
        super().save_model(request, obj, form, change)

        if is_new and obj.upload:
            print("QUEUING TRANSCODE JOB")
            transcode_video.delay(obj.id, obj.upload.path)
        else:
            print("CONDITION FAILED - is_new:", is_new, "upload:", obj.upload)