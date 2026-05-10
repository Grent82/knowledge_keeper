from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.access_control.services import visible_media_items_queryset
from apps.common.permissions import IsOwnerRole
from apps.media_library.models import MediaItem

from .models import PlaybackProgress, Summary, Transcript
from .serializers import PlaybackProgressSerializer, SummarySerializer, TranscriptSerializer


class PlaybackProgressViewSet(ModelViewSet):
    serializer_class = PlaybackProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlaybackProgress.objects.filter(user=self.request.user).select_related("media_item")

    def perform_create(self, serializer):
        media_item = serializer.validated_data["media_item"]
        if not visible_media_items_queryset(self.request.user).filter(id=media_item.id).exists():
            self.permission_denied(
                self.request,
                message="You cannot create playback progress for inaccessible media.",
            )
        serializer.save(user=self.request.user)


class TranscriptViewSet(ModelViewSet):
    serializer_class = TranscriptSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        return Transcript.objects.filter(media_item__owner=self.request.user).select_related(
            "media_item"
        )

    def perform_create(self, serializer):
        media_item = serializer.validated_data["media_item"]
        if media_item.owner_id != self.request.user.id:
            self.permission_denied(self.request, message="Only the owner can create artifacts.")
        serializer.save()


class SummaryViewSet(ModelViewSet):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        return Summary.objects.filter(media_item__owner=self.request.user).select_related(
            "media_item", "transcript"
        )

    def perform_create(self, serializer):
        media_item: MediaItem = serializer.validated_data["media_item"]
        if media_item.owner_id != self.request.user.id:
            self.permission_denied(self.request, message="Only the owner can create artifacts.")
        serializer.save()
