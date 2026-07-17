import os
from django.conf import settings
from django.http import HttpResponse, FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from video_app.models import Video
from .serializers import VideoSerializer
from django.core.cache import cache


class VideoListView(APIView):
    """Return all HLS-ready videos, cached in Redis for 5 minutes."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the cached video list or generate it from the database."""
        cached = cache.get("video_list")
        if cached:
            return Response(cached)

        videos = Video.objects.filter(hls_ready=True).select_related("category")
        serializer = VideoSerializer(videos, many=True, context={"request": request})
        cache.set("video_list", serializer.data, timeout=60 * 5)
        return Response(serializer.data)


class PlaylistView(APIView):
    """Serve an HLS playlist for a video and resolution."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """
        Verify the video exists and is ready, validate the resolution,
        then serve the .m3u8 playlist file with the correct content type
        so HLS players can parse it correctly.
        """
        try:
            video = Video.objects.get(pk=movie_id, hls_ready=True)
        except Video.DoesNotExist:
            return Response(
                {"error": "Video not found or not ready."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if resolution not in ["480p", "720p", "1080p"]:
            return Response(
                {"error": "Invalid resolution."}, status=status.HTTP_400_BAD_REQUEST
            )

        playlist_path = os.path.join(
            settings.HLS_ROOT, str(movie_id), resolution, "index.m3u8"
        )

        if not os.path.exists(playlist_path):
            return Response(
                {"error": f"Playlist not found at {playlist_path}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with open(playlist_path, "r") as f:
            content = f.read()

        return HttpResponse(content, content_type="application/vnd.apple.mpegurl")


class SegmentView(APIView):
    """Serve individual HLS video segments."""

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """
        Validate the resolution and segment name to prevent path traversal attacks,
        then serve the .ts segment file as a binary stream.
        """
        if resolution not in ["480p", "720p", "1080p"]:
            return Response(
                {"error": "Invalid resolution."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not segment.endswith(".ts") or "/" in segment or ".." in segment:
            return Response(
                {"error": "Invalid segment."}, status=status.HTTP_400_BAD_REQUEST
            )

        segment_path = os.path.join(
            settings.HLS_ROOT, str(movie_id), resolution, segment
        )

        if not os.path.exists(segment_path):
            return Response(
                {"error": "Segment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        return FileResponse(open(segment_path, "rb"), content_type="video/MP2T")
