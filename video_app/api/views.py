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
from video_app.helpers import get_video_or_404, is_valid_resolution, get_playlist_path, read_playlist, get_segment_path, is_valid_segment

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
    """Serves the HLS playlist file for a specific video and resolution."""
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """
        Verify the video exists and is ready, validate the resolution,
        then serve the .m3u8 playlist file with the correct content type
        so HLS players can parse it correctly.
        """
        if not get_video_or_404(movie_id):
            return Response(
                {"error": "Video not found or not ready."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not is_valid_resolution(resolution):
            return Response(
                {"error": "Invalid resolution."}, status=status.HTTP_400_BAD_REQUEST
            )

        playlist_path = get_playlist_path(movie_id, resolution)
        content = read_playlist(playlist_path)

        if content is None:
            return Response(
                {"error": f"Playlist not found at {playlist_path}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return HttpResponse(content, content_type="application/vnd.apple.mpegurl")


class SegmentView(APIView):
    """Serves individual HLS video segments."""
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """
        Validate the resolution and segment name to prevent path traversal attacks,
        then serve the .ts segment file as a binary stream.
        """
        if not is_valid_resolution(resolution):
            return Response({"error": "Invalid resolution."}, status=status.HTTP_400_BAD_REQUEST)
        if not is_valid_segment(segment):
            return Response({"error": "Invalid segment."}, status=status.HTTP_400_BAD_REQUEST)

        segment_path = get_segment_path(movie_id, resolution, segment)
        if not os.path.exists(segment_path):
            return Response({"error": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(segment_path, "rb"), content_type="video/MP2T")
