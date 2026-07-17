from rest_framework import serializers
from video_app.models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Serialize video metadata for the API."""
    
    thumbnail_url = serializers.SerializerMethodField()
    category = serializers.StringRelatedField()

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "description",
            "thumbnail_url",
            "category",
            "created_at",
        ]

    def get_thumbnail_url(self, obj):
        """
        Build an absolute thumbnail URL using the request context, so the response
        contains a complete URL rather than a relative path. Returns None if no
        thumbnail is set or no request is available in the context.
        """
        request = self.context.get("request")
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
