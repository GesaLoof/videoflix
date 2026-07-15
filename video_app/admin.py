from django.contrib import admin
from .models import Video, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "hls_ready", "created_at"]
    readonly_fields = ["hls_ready", "created_at"]
