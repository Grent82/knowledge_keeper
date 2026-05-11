from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.access_control.services import visible_media_items_queryset
from apps.common.permissions import IsOwnerRole
from apps.media_library.models import MediaItem

from .models import PlaybackProgress, Summary, Transcript, TranscriptSegment
from .serializers import (
    PlaybackProgressSerializer,
    SummarySerializer,
    TranscriptSegmentSerializer,
    TranscriptSerializer,
)


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
        queryset = Transcript.objects.filter(media_item__owner=self.request.user).select_related(
            "media_item"
        )
        media_item_id = self.request.query_params.get("media_item")
        if media_item_id:
            queryset = queryset.filter(media_item_id=media_item_id)
        return queryset

    def perform_create(self, serializer):
        media_item = serializer.validated_data["media_item"]
        if media_item.owner_id != self.request.user.id:
            self.permission_denied(self.request, message="Only the owner can create artifacts.")
        serializer.save()


class SummaryViewSet(ModelViewSet):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        queryset = Summary.objects.filter(media_item__owner=self.request.user).select_related(
            "media_item", "transcript"
        )
        media_item_id = self.request.query_params.get("media_item")
        if media_item_id:
            queryset = queryset.filter(media_item_id=media_item_id)
        return queryset

    def perform_create(self, serializer):
        media_item: MediaItem = serializer.validated_data["media_item"]
        if media_item.owner_id != self.request.user.id:
            self.permission_denied(self.request, message="Only the owner can create artifacts.")
        serializer.save()


class TranscriptSegmentViewSet(ModelViewSet):
    serializer_class = TranscriptSegmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        queryset = TranscriptSegment.objects.filter(
            transcript__media_item__owner=self.request.user
        ).select_related("transcript")
        transcript_id = self.request.query_params.get("transcript")
        if transcript_id:
            queryset = queryset.filter(transcript_id=transcript_id)
        return queryset.order_by("sequence_number")
